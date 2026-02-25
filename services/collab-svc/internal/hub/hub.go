// Package hub implements a scenario-scoped WebSocket message hub.
//
// Architecture:
//   - One Hub per server; scenarios are modeled as "rooms" (map[scenarioID]room).
//   - Each Client holds a WebSocket connection and a send channel.
//   - The Hub goroutine serialises all register/unregister/broadcast operations.
//   - A Redis subscriber goroutine forwards sim events from sim-orchestrator to
//     connected clients.
//   - Map control: one user per room may hold exclusive map edit rights.
package hub

import (
	"encoding/json"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"go.uber.org/zap"
)

const (
	writeWait      = 10 * time.Second
	pongWait       = 60 * time.Second
	pingPeriod     = (pongWait * 9) / 10
	maxMessageSize = 64 * 1024 // 64 KiB
)

// Message is a generic envelope sent between clients and the hub.
type Message struct {
	Type       string          `json:"type"`
	ScenarioID string          `json:"scenario_id,omitempty"`
	UserID     string          `json:"user_id,omitempty"`
	Payload    json.RawMessage `json:"payload,omitempty"`
}

// Client represents a single WebSocket connection.
type Client struct {
	hub        *Hub
	conn       *websocket.Conn
	send       chan []byte
	ScenarioID string
	UserID     string
	Roles      []string
}

// Hub maintains the set of active clients and broadcasts messages to them.
type Hub struct {
	mu          sync.RWMutex
	rooms       map[string]map[*Client]struct{} // scenarioID → set of clients
	controllers map[string]string               // scenarioID → userID holding map control
	register    chan *Client
	unregister  chan *Client
	broadcast   chan broadcastMsg
	log         *zap.Logger
}

type broadcastMsg struct {
	scenarioID string
	data       []byte
}

// New creates and starts a Hub.
func New(log *zap.Logger) *Hub {
	h := &Hub{
		rooms:       make(map[string]map[*Client]struct{}),
		controllers: make(map[string]string),
		register:    make(chan *Client, 64),
		unregister:  make(chan *Client, 64),
		broadcast:   make(chan broadcastMsg, 256),
		log:         log,
	}
	go h.run()
	return h
}

// Broadcast sends a message to all clients in a scenario room.
func (h *Hub) Broadcast(scenarioID string, data []byte) {
	h.broadcast <- broadcastMsg{scenarioID: scenarioID, data: data}
}

// Register adds a client to its scenario room.
func (h *Hub) Register(c *Client) {
	h.register <- c
}

// Unregister removes a client from its scenario room.
func (h *Hub) Unregister(c *Client) {
	h.unregister <- c
}

// GetController returns the userID of the user who currently holds map control
// in the given scenario room, or "" if no one holds control.
func (h *Hub) GetController(scenarioID string) string {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return h.controllers[scenarioID]
}

// RequestMapControl attempts to grant map control to userID in scenarioID.
// Returns true if control was granted (room was empty or requester already owns it),
// false if another user already holds control.
// canControl must be true (caller validates role/permission before calling).
func (h *Hub) RequestMapControl(scenarioID, userID string) bool {
	h.mu.Lock()
	defer h.mu.Unlock()

	current := h.controllers[scenarioID]
	if current != "" && current != userID {
		return false
	}
	h.controllers[scenarioID] = userID
	return true
}

// ReleaseMapControl releases map control held by userID in scenarioID.
// If userID does not hold control, this is a no-op.
func (h *Hub) ReleaseMapControl(scenarioID, userID string) {
	h.mu.Lock()
	defer h.mu.Unlock()
	if h.controllers[scenarioID] == userID {
		delete(h.controllers, scenarioID)
	}
}

// RevokeMapControl forcibly clears map control for a scenario (admin use).
func (h *Hub) RevokeMapControl(scenarioID string) {
	h.mu.Lock()
	defer h.mu.Unlock()
	delete(h.controllers, scenarioID)
}

// Presence returns the list of user IDs currently connected to a scenario room.
func (h *Hub) Presence(scenarioID string) []string {
	h.mu.RLock()
	defer h.mu.RUnlock()
	room := h.rooms[scenarioID]
	users := make([]string, 0, len(room))
	seen := make(map[string]struct{})
	for c := range room {
		if _, ok := seen[c.UserID]; !ok {
			users = append(users, c.UserID)
			seen[c.UserID] = struct{}{}
		}
	}
	return users
}

func (h *Hub) run() {
	for {
		select {
		case c := <-h.register:
			h.mu.Lock()
			if h.rooms[c.ScenarioID] == nil {
				h.rooms[c.ScenarioID] = make(map[*Client]struct{})
			}
			h.rooms[c.ScenarioID][c] = struct{}{}
			h.mu.Unlock()
			h.log.Info("client joined",
				zap.String("scenario_id", c.ScenarioID),
				zap.String("user_id", c.UserID),
			)

		case c := <-h.unregister:
			h.mu.Lock()
			if room, ok := h.rooms[c.ScenarioID]; ok {
				delete(room, c)
				if len(room) == 0 {
					delete(h.rooms, c.ScenarioID)
				}
			}
			// Release map control if this client held it
			if h.controllers[c.ScenarioID] == c.UserID {
				delete(h.controllers, c.ScenarioID)
				// Notify remaining clients that control was released
				releaseMsg, _ := json.Marshal(Message{
					Type:       "map:control:released",
					ScenarioID: c.ScenarioID,
					UserID:     c.UserID,
				})
				room := h.rooms[c.ScenarioID]
				for rc := range room {
					select {
					case rc.send <- releaseMsg:
					default:
					}
				}
			}
			h.mu.Unlock()
			close(c.send)
			h.log.Info("client left",
				zap.String("scenario_id", c.ScenarioID),
				zap.String("user_id", c.UserID),
			)

		case msg := <-h.broadcast:
			h.mu.RLock()
			room := h.rooms[msg.scenarioID]
			h.mu.RUnlock()
			for c := range room {
				select {
				case c.send <- msg.data:
				default:
					// Slow client: drop the message to avoid blocking.
					h.log.Warn("dropping message for slow client",
						zap.String("user_id", c.UserID),
					)
				}
			}
		}
	}
}

// ServeWS upgrades the HTTP connection to WebSocket and starts read/write pumps.
func (h *Hub) ServeWS(conn *websocket.Conn, scenarioID, userID string, roles []string) {
	c := &Client{
		hub:        h,
		conn:       conn,
		send:       make(chan []byte, 256),
		ScenarioID: scenarioID,
		UserID:     userID,
		Roles:      roles,
	}
	h.Register(c)

	// Announce join to the room
	joinMsg, _ := json.Marshal(Message{
		Type:       "user:join",
		ScenarioID: scenarioID,
		UserID:     userID,
	})
	h.Broadcast(scenarioID, joinMsg)

	go c.writePump()
	go c.readPump()
}

// readPump reads messages from the WebSocket and fans them out to the scenario room.
func (c *Client) readPump() {
	defer func() {
		c.hub.Unregister(c)
		c.conn.Close() //nolint:errcheck
	}()

	c.conn.SetReadLimit(maxMessageSize)
	c.conn.SetReadDeadline(time.Now().Add(pongWait)) //nolint:errcheck
	c.conn.SetPongHandler(func(string) error {
		c.conn.SetReadDeadline(time.Now().Add(pongWait)) //nolint:errcheck
		return nil
	})

	for {
		_, raw, err := c.conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err,
				websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				c.hub.log.Warn("ws read error", zap.Error(err), zap.String("user_id", c.UserID))
			}
			break
		}

		var msg Message
		if err := json.Unmarshal(raw, &msg); err != nil {
			c.hub.log.Warn("invalid message", zap.Error(err))
			continue
		}
		msg.UserID = c.UserID
		msg.ScenarioID = c.ScenarioID

		// Handle map control request inline
		if msg.Type == "map:control:request" {
			c.handleMapControlRequest()
			continue
		}
		if msg.Type == "map:control:release" {
			c.hub.ReleaseMapControl(c.ScenarioID, c.UserID)
			releaseMsg, _ := json.Marshal(Message{
				Type:       "map:control:released",
				ScenarioID: c.ScenarioID,
				UserID:     c.UserID,
			})
			c.hub.Broadcast(c.ScenarioID, releaseMsg)
			continue
		}

		out, err := json.Marshal(msg)
		if err != nil {
			c.hub.log.Warn("marshal error", zap.Error(err))
			continue
		}
		c.hub.Broadcast(c.ScenarioID, out)
	}
}

// handleMapControlRequest processes a map control request from this client.
func (c *Client) handleMapControlRequest() {
	if !hasMapControlRole(c.Roles) {
		denied, _ := json.Marshal(Message{
			Type:       "map:control:denied",
			ScenarioID: c.ScenarioID,
			UserID:     c.UserID,
		})
		select {
		case c.send <- denied:
		default:
		}
		return
	}

	if c.hub.RequestMapControl(c.ScenarioID, c.UserID) {
		granted, _ := json.Marshal(Message{
			Type:       "map:control:granted",
			ScenarioID: c.ScenarioID,
			UserID:     c.UserID,
		})
		c.hub.Broadcast(c.ScenarioID, granted)
	} else {
		controller := c.hub.GetController(c.ScenarioID)
		type busyPayload struct {
			ControllerID string `json:"controller_id"`
		}
		payload, _ := json.Marshal(busyPayload{ControllerID: controller})
		busy, _ := json.Marshal(Message{
			Type:       "map:control:busy",
			ScenarioID: c.ScenarioID,
			UserID:     c.UserID,
			Payload:    payload,
		})
		select {
		case c.send <- busy:
		default:
		}
	}
}

// hasMapControlRole returns true if the provided roles include any role that
// is allowed to request map control (planner, commander, sim_operator, admin).
func hasMapControlRole(roles []string) bool {
	allowed := map[string]struct{}{
		"planner":      {},
		"commander":    {},
		"sim_operator": {},
		"admin":        {},
	}
	for _, r := range roles {
		if _, ok := allowed[r]; ok {
			return true
		}
	}
	return false
}

// writePump pumps messages from the send channel to the WebSocket connection.
func (c *Client) writePump() {
	ticker := time.NewTicker(pingPeriod)
	defer func() {
		ticker.Stop()
		c.conn.Close() //nolint:errcheck
	}()

	for {
		select {
		case msg, ok := <-c.send:
			c.conn.SetWriteDeadline(time.Now().Add(writeWait)) //nolint:errcheck
			if !ok {
				c.conn.WriteMessage(websocket.CloseMessage, []byte{}) //nolint:errcheck
				return
			}
			if err := c.conn.WriteMessage(websocket.TextMessage, msg); err != nil {
				return
			}
		case <-ticker.C:
			c.conn.SetWriteDeadline(time.Now().Add(writeWait)) //nolint:errcheck
			if err := c.conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

// SubscribeSimEvents subscribes to Redis pub/sub for a run's events and broadcasts
// them to the scenario room.  The concrete implementation is wired up in
// handlers/ws.go via bridgeRedisToRoom, which subscribes to the per-scenario
// "collab:{scenarioID}" channel.  This placeholder is kept here to document the
// intended interface between the hub and the Redis bridge.
func (h *Hub) SubscribeSimEvents(scenarioID string) {
	// See handlers/ws.go: WSHandler.bridgeRedisToRoom for the implementation.
}
