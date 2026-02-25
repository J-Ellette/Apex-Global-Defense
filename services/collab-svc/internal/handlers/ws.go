package handlers

import (
	"context"
	"encoding/json"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/gorilla/websocket"
	"github.com/redis/go-redis/v9"
	"go.uber.org/zap"

	"github.com/j-ellette/apex-global-defense/services/collab-svc/internal/hub"
)

var upgrader = websocket.Upgrader{
	CheckOrigin:     func(r *http.Request) bool { return true },
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
}

// WSHandler handles WebSocket upgrade and scenario room management.
type WSHandler struct {
	hub       *hub.Hub
	rdb       *redis.Client
	jwtSecret []byte
	log       *zap.Logger
}

// NewWSHandler creates a new WebSocket handler.
func NewWSHandler(h *hub.Hub, rdb *redis.Client, jwtSecret string, log *zap.Logger) *WSHandler {
	return &WSHandler{
		hub:       h,
		rdb:       rdb,
		jwtSecret: []byte(jwtSecret),
		log:       log,
	}
}

// ServeWS is the Gin handler for GET /ws/:scenario_id
func (wh *WSHandler) ServeWS(c *gin.Context) {
	scenarioID := c.Param("scenario_id")
	if scenarioID == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "missing scenario_id"})
		return
	}

	// Validate JWT from query param or Authorization header.
	tokenStr := c.Query("token")
	if tokenStr == "" {
		auth := c.GetHeader("Authorization")
		if len(auth) > 7 && auth[:7] == "Bearer " {
			tokenStr = auth[7:]
		}
	}
	if tokenStr == "" {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "missing token"})
		return
	}

	claims, err := wh.validateJWT(tokenStr)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
		return
	}

	userID, _ := claims["uid"].(string)
	roles := extractRoles(claims)

	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		wh.log.Warn("websocket upgrade failed", zap.Error(err))
		return
	}

	wh.hub.ServeWS(conn, scenarioID, userID, roles)

	// Subscribe to Redis sim events for this scenario and fan out to the room.
	go wh.bridgeRedisToRoom(scenarioID)
}

// bridgeRedisToRoom subscribes to "sim:*" on Redis and broadcasts to the room.
func (wh *WSHandler) bridgeRedisToRoom(scenarioID string) {
	ctx := context.Background()
	pubsub := wh.rdb.Subscribe(ctx, "collab:"+scenarioID)
	defer pubsub.Close()

	ch := pubsub.Channel()
	for msg := range ch {
		envelope := map[string]interface{}{
			"type":    "sim:event",
			"payload": json.RawMessage(msg.Payload),
		}
		data, err := json.Marshal(envelope)
		if err != nil {
			wh.log.Warn("marshal error in redis bridge", zap.Error(err))
			continue
		}
		wh.hub.Broadcast(scenarioID, data)
	}
}

func (wh *WSHandler) validateJWT(tokenStr string) (jwt.MapClaims, error) {
	token, err := jwt.Parse(tokenStr, func(t *jwt.Token) (interface{}, error) {
		if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, jwt.ErrSignatureInvalid
		}
		return wh.jwtSecret, nil
	})
	if err != nil {
		return nil, err
	}
	if !token.Valid {
		return nil, jwt.ErrTokenInvalidClaims
	}
	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok {
		return nil, jwt.ErrTokenInvalidClaims
	}
	return claims, nil
}

// extractRoles parses the "roles" claim from JWT MapClaims into a []string.
func extractRoles(claims jwt.MapClaims) []string {
	raw, ok := claims["roles"]
	if !ok {
		return nil
	}
	switch v := raw.(type) {
	case []interface{}:
		roles := make([]string, 0, len(v))
		for _, r := range v {
			if s, ok := r.(string); ok {
				roles = append(roles, s)
			}
		}
		return roles
	case []string:
		return v
	}
	return nil
}

// PresenceHandler returns the list of connected users in a scenario room.
func (wh *WSHandler) PresenceHandler(c *gin.Context) {
	scenarioID := c.Param("scenario_id")
	users := wh.hub.Presence(scenarioID)
	controller := wh.hub.GetController(scenarioID)
	c.JSON(http.StatusOK, gin.H{
		"users":      users,
		"controller": controller,
	})
}

// GetMapControlHandler returns the current map controller for a scenario room.
func (wh *WSHandler) GetMapControlHandler(c *gin.Context) {
	scenarioID := c.Param("scenario_id")
	controller := wh.hub.GetController(scenarioID)
	c.JSON(http.StatusOK, gin.H{"controller_id": controller})
}

// RequestMapControlHandler lets an authenticated user request map control via REST.
func (wh *WSHandler) RequestMapControlHandler(c *gin.Context) {
	scenarioID := c.Param("scenario_id")

	claims, err := wh.authFromRequest(c)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
		return
	}
	userID, _ := claims["uid"].(string)
	roles := extractRoles(claims)

	if !hasMapControlRole(roles) {
		c.JSON(http.StatusForbidden, gin.H{"error": "role does not permit map control"})
		return
	}

	if wh.hub.RequestMapControl(scenarioID, userID) {
		c.JSON(http.StatusOK, gin.H{"controller_id": userID, "granted": true})
	} else {
		controller := wh.hub.GetController(scenarioID)
		c.JSON(http.StatusConflict, gin.H{
			"granted":       false,
			"controller_id": controller,
			"error":         "map control held by another user",
		})
	}
}

// ReleaseMapControlHandler lets the current controller release map control via REST.
func (wh *WSHandler) ReleaseMapControlHandler(c *gin.Context) {
	scenarioID := c.Param("scenario_id")

	claims, err := wh.authFromRequest(c)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
		return
	}
	userID, _ := claims["uid"].(string)

	wh.hub.ReleaseMapControl(scenarioID, userID)
	c.JSON(http.StatusOK, gin.H{"released": true})
}

// authFromRequest extracts and validates the JWT from the Authorization header.
func (wh *WSHandler) authFromRequest(c *gin.Context) (jwt.MapClaims, error) {
	tokenStr := c.GetHeader("Authorization")
	if len(tokenStr) > 7 && tokenStr[:7] == "Bearer " {
		tokenStr = tokenStr[7:]
	}
	return wh.validateJWT(tokenStr)
}

// hasMapControlRole returns true if roles contain a map-control-eligible role.
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
