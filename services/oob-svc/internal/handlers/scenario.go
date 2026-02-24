package handlers

import (
	"context"
	"errors"
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/j-ellette/apex-global-defense/services/oob-svc/internal/models"
	"github.com/j-ellette/apex-global-defense/services/oob-svc/internal/store"
	"go.uber.org/zap"
)

// scenarioStore defines the persistence operations required by ScenarioHandler.
type scenarioStore interface {
	ListScenarios(ctx context.Context, orgID string) ([]models.Scenario, error)
	GetScenario(ctx context.Context, id uuid.UUID) (*models.Scenario, error)
	CreateScenario(ctx context.Context, req models.CreateScenarioRequest, userID, orgID uuid.UUID) (*models.Scenario, error)
	UpdateScenario(ctx context.Context, id uuid.UUID, req models.UpdateScenarioRequest) (*models.Scenario, error)
	DeleteScenario(ctx context.Context, id uuid.UUID) error
	BranchScenario(ctx context.Context, sourceID uuid.UUID, branchName string, userID uuid.UUID) (*models.Scenario, error)
}

// ScenarioHandler holds all scenario endpoint handlers.
type ScenarioHandler struct {
	store scenarioStore
	log   *zap.Logger
}

// NewScenarioHandler constructs a ScenarioHandler.
func NewScenarioHandler(s scenarioStore, log *zap.Logger) *ScenarioHandler {
	return &ScenarioHandler{store: s, log: log}
}

// ListScenarios godoc
// @Summary      List scenarios for the caller's org
// @Tags         scenarios
// @Produce      json
// @Success      200 {array} models.Scenario
// @Router       /scenarios [get]
func (h *ScenarioHandler) ListScenarios(c *gin.Context) {
	claims := claimsFromCtx(c)
	scenarios, err := h.store.ListScenarios(c.Request.Context(), claims.OrgID)
	if err != nil {
		h.log.Error("list scenarios", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}
	c.JSON(http.StatusOK, scenarios)
}

// GetScenario godoc
// @Summary      Get a scenario by ID
// @Tags         scenarios
// @Produce      json
// @Param        id path string true "Scenario UUID"
// @Success      200 {object} models.Scenario
// @Failure      404 {object} map[string]string
// @Router       /scenarios/{id} [get]
func (h *ScenarioHandler) GetScenario(c *gin.Context) {
	id, ok := parseUUID(c, "id")
	if !ok {
		return
	}

	scenario, err := h.store.GetScenario(c.Request.Context(), id)
	if err != nil {
		if errors.Is(err, store.ErrNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "scenario_not_found"})
			return
		}
		h.log.Error("get scenario", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}
	c.JSON(http.StatusOK, scenario)
}

// CreateScenario godoc
// @Summary      Create a new scenario
// @Tags         scenarios
// @Accept       json
// @Produce      json
// @Param        body body models.CreateScenarioRequest true "Scenario payload"
// @Success      201 {object} models.Scenario
// @Router       /scenarios [post]
func (h *ScenarioHandler) CreateScenario(c *gin.Context) {
	var req models.CreateScenarioRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	claims := claimsFromCtx(c)
	userID, _ := uuid.Parse(claims.UserID)
	orgID, _ := uuid.Parse(claims.OrgID)

	scenario, err := h.store.CreateScenario(c.Request.Context(), req, userID, orgID)
	if err != nil {
		h.log.Error("create scenario", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}
	c.JSON(http.StatusCreated, scenario)
}

// UpdateScenario godoc
// @Summary      Update a scenario
// @Tags         scenarios
// @Accept       json
// @Produce      json
// @Param        id   path string true "Scenario UUID"
// @Param        body body models.UpdateScenarioRequest true "Update payload"
// @Success      200 {object} models.Scenario
// @Router       /scenarios/{id} [put]
func (h *ScenarioHandler) UpdateScenario(c *gin.Context) {
	id, ok := parseUUID(c, "id")
	if !ok {
		return
	}

	var req models.UpdateScenarioRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	scenario, err := h.store.UpdateScenario(c.Request.Context(), id, req)
	if err != nil {
		if errors.Is(err, store.ErrNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "scenario_not_found"})
			return
		}
		h.log.Error("update scenario", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}
	c.JSON(http.StatusOK, scenario)
}

// DeleteScenario godoc
// @Summary      Delete a scenario
// @Tags         scenarios
// @Param        id path string true "Scenario UUID"
// @Success      204
// @Router       /scenarios/{id} [delete]
func (h *ScenarioHandler) DeleteScenario(c *gin.Context) {
	id, ok := parseUUID(c, "id")
	if !ok {
		return
	}

	if err := h.store.DeleteScenario(c.Request.Context(), id); err != nil {
		if errors.Is(err, store.ErrNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "scenario_not_found"})
			return
		}
		h.log.Error("delete scenario", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}
	c.Status(http.StatusNoContent)
}

// BranchScenario godoc
// @Summary      Branch a scenario
// @Tags         scenarios
// @Accept       json
// @Produce      json
// @Param        id   path string true "Source scenario UUID"
// @Param        body body map[string]string true `{"name": "Branch name"}`
// @Success      201 {object} models.Scenario
// @Router       /scenarios/{id}/branch [post]
func (h *ScenarioHandler) BranchScenario(c *gin.Context) {
	id, ok := parseUUID(c, "id")
	if !ok {
		return
	}

	var body struct {
		Name string `json:"name" binding:"required"`
	}
	if err := c.ShouldBindJSON(&body); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	claims := claimsFromCtx(c)
	userID, _ := uuid.Parse(claims.UserID)

	scenario, err := h.store.BranchScenario(c.Request.Context(), id, body.Name, userID)
	if err != nil {
		if errors.Is(err, store.ErrNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "scenario_not_found"})
			return
		}
		h.log.Error("branch scenario", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}
	c.JSON(http.StatusCreated, scenario)
}

// ── helpers ───────────────────────────────────────────────────────────────────

func claimsFromCtx(c *gin.Context) *models.Claims {
	return c.MustGet("claims").(*models.Claims)
}

func parseUUID(c *gin.Context, param string) (uuid.UUID, bool) {
	raw := c.Param(param)
	id, err := uuid.Parse(raw)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid_id"})
		return uuid.Nil, false
	}
	return id, true
}
