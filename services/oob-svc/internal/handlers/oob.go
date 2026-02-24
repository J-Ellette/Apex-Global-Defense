package handlers

import (
	"context"
	"errors"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/j-ellette/apex-global-defense/services/oob-svc/internal/models"
	"github.com/j-ellette/apex-global-defense/services/oob-svc/internal/store"
	"go.uber.org/zap"
)

// oobStore defines the persistence operations required by OOBHandler.
type oobStore interface {
	ListCountries(ctx context.Context) ([]models.Country, error)
	GetCountry(ctx context.Context, code string) (*models.Country, error)
	ListUnitsByCountry(ctx context.Context, code string) ([]models.MilitaryUnit, error)
	GetUnit(ctx context.Context, id uuid.UUID) (*models.MilitaryUnit, error)
	CreateUnit(ctx context.Context, req models.CreateUnitRequest) (*models.MilitaryUnit, error)
	UpdateUnit(ctx context.Context, id uuid.UUID, req models.UpdateUnitRequest) (*models.MilitaryUnit, error)
	DeleteUnit(ctx context.Context, id uuid.UUID) error
	CountryStrength(ctx context.Context, code string, asOf *time.Time) (*models.CountryStrength, error)
	ListEquipmentCatalog(ctx context.Context) ([]models.EquipmentCatalogItem, error)
}

// OOBHandler holds all OOB endpoint handlers.
type OOBHandler struct {
	store oobStore
	log   *zap.Logger
}

// NewOOBHandler constructs an OOBHandler.
func NewOOBHandler(s oobStore, log *zap.Logger) *OOBHandler {
	return &OOBHandler{store: s, log: log}
}

// ListCountries godoc
// @Summary      List all countries
// @Tags         oob
// @Produce      json
// @Success      200 {array} models.Country
// @Router       /oob/countries [get]
func (h *OOBHandler) ListCountries(c *gin.Context) {
	countries, err := h.store.ListCountries(c.Request.Context())
	if err != nil {
		h.log.Error("list countries", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}
	if countries == nil {
		countries = []models.Country{}
	}
	c.JSON(http.StatusOK, countries)
}

// GetCountry godoc
// @Summary      Get a country by ISO code
// @Tags         oob
// @Produce      json
// @Param        code path string true "ISO 3166-1 alpha-3 code"
// @Success      200 {object} models.Country
// @Failure      404 {object} map[string]string
// @Router       /oob/countries/{code} [get]
func (h *OOBHandler) GetCountry(c *gin.Context) {
	code := c.Param("code")
	country, err := h.store.GetCountry(c.Request.Context(), code)
	if err != nil {
		if errors.Is(err, store.ErrNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "country_not_found"})
			return
		}
		h.log.Error("get country", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}
	c.JSON(http.StatusOK, country)
}

// ListForces godoc
// @Summary      List military units for a country
// @Tags         oob
// @Produce      json
// @Param        code path string true "ISO 3166-1 alpha-3 code"
// @Success      200 {array} models.MilitaryUnit
// @Failure      404 {object} map[string]string
// @Router       /oob/countries/{code}/forces [get]
func (h *OOBHandler) ListForces(c *gin.Context) {
	code := c.Param("code")
	// Validate country exists first.
	if _, err := h.store.GetCountry(c.Request.Context(), code); err != nil {
		if errors.Is(err, store.ErrNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "country_not_found"})
			return
		}
		h.log.Error("get country for forces", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}

	units, err := h.store.ListUnitsByCountry(c.Request.Context(), code)
	if err != nil {
		h.log.Error("list forces", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}
	if units == nil {
		units = []models.MilitaryUnit{}
	}
	c.JSON(http.StatusOK, units)
}

// GetUnit godoc
// @Summary      Get a military unit by ID
// @Tags         oob
// @Produce      json
// @Param        id path string true "Unit UUID"
// @Success      200 {object} models.MilitaryUnit
// @Failure      400 {object} map[string]string
// @Failure      404 {object} map[string]string
// @Router       /oob/units/{id} [get]
func (h *OOBHandler) GetUnit(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid_unit_id"})
		return
	}

	unit, err := h.store.GetUnit(c.Request.Context(), id)
	if err != nil {
		if errors.Is(err, store.ErrNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "unit_not_found"})
			return
		}
		h.log.Error("get unit", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}
	c.JSON(http.StatusOK, unit)
}

// CreateUnit godoc
// @Summary      Create a military unit
// @Tags         oob
// @Accept       json
// @Produce      json
// @Param        body body models.CreateUnitRequest true "Unit data"
// @Success      201 {object} models.MilitaryUnit
// @Failure      400 {object} map[string]string
// @Router       /oob/units [post]
func (h *OOBHandler) CreateUnit(c *gin.Context) {
	var req models.CreateUnitRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	unit, err := h.store.CreateUnit(c.Request.Context(), req)
	if err != nil {
		h.log.Error("create unit", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}
	c.JSON(http.StatusCreated, unit)
}

// UpdateUnit godoc
// @Summary      Update a military unit
// @Tags         oob
// @Accept       json
// @Produce      json
// @Param        id   path string                   true "Unit UUID"
// @Param        body body models.UpdateUnitRequest true "Fields to update"
// @Success      200 {object} models.MilitaryUnit
// @Failure      400 {object} map[string]string
// @Failure      404 {object} map[string]string
// @Router       /oob/units/{id} [put]
func (h *OOBHandler) UpdateUnit(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid_unit_id"})
		return
	}

	var req models.UpdateUnitRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	unit, err := h.store.UpdateUnit(c.Request.Context(), id, req)
	if err != nil {
		if errors.Is(err, store.ErrNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "unit_not_found"})
			return
		}
		h.log.Error("update unit", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}
	c.JSON(http.StatusOK, unit)
}

// DeleteUnit godoc
// @Summary      Delete a military unit
// @Tags         oob
// @Param        id path string true "Unit UUID"
// @Success      204
// @Failure      400 {object} map[string]string
// @Failure      404 {object} map[string]string
// @Router       /oob/units/{id} [delete]
func (h *OOBHandler) DeleteUnit(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid_unit_id"})
		return
	}

	if err := h.store.DeleteUnit(c.Request.Context(), id); err != nil {
		if errors.Is(err, store.ErrNotFound) {
			c.JSON(http.StatusNotFound, gin.H{"error": "unit_not_found"})
			return
		}
		h.log.Error("delete unit", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}
	c.Status(http.StatusNoContent)
}

// UnitHistory godoc
// @Summary      Get unit change history (placeholder)
// @Tags         oob
// @Param        id path string true "Unit UUID"
// @Success      200 {array} object
// @Failure      400 {object} map[string]string
// @Router       /oob/units/{id}/history [get]
func (h *OOBHandler) UnitHistory(c *gin.Context) {
	if _, err := uuid.Parse(c.Param("id")); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid_unit_id"})
		return
	}
	// Unit versioning will be implemented in a later phase.
	c.JSON(http.StatusOK, []interface{}{})
}

// CompareCountries godoc
// @Summary      Compare Order of Battle between two countries
// @Tags         oob
// @Accept       json
// @Produce      json
// @Param        body body models.CompareRequest true "Country codes to compare"
// @Success      200 {object} models.CompareResponse
// @Failure      400 {object} map[string]string
// @Router       /oob/compare [post]
func (h *OOBHandler) CompareCountries(c *gin.Context) {
	var req models.CompareRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	strengthA, err := h.store.CountryStrength(c.Request.Context(), req.CountryA, req.AsOf)
	if err != nil {
		if errors.Is(err, store.ErrNotFound) {
			c.JSON(http.StatusBadRequest, gin.H{"error": "country_a_not_found"})
			return
		}
		h.log.Error("compare country A", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}

	strengthB, err := h.store.CountryStrength(c.Request.Context(), req.CountryB, req.AsOf)
	if err != nil {
		if errors.Is(err, store.ErrNotFound) {
			c.JSON(http.StatusBadRequest, gin.H{"error": "country_b_not_found"})
			return
		}
		h.log.Error("compare country B", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}

	c.JSON(http.StatusOK, models.CompareResponse{
		CountryA: *strengthA,
		CountryB: *strengthB,
	})
}

// ListEquipmentCatalog godoc
// @Summary      List equipment catalog
// @Tags         oob
// @Produce      json
// @Success      200 {array} models.EquipmentCatalogItem
// @Router       /oob/equipment/catalog [get]
func (h *OOBHandler) ListEquipmentCatalog(c *gin.Context) {
	items, err := h.store.ListEquipmentCatalog(c.Request.Context())
	if err != nil {
		h.log.Error("list equipment catalog", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "internal_server_error"})
		return
	}
	if items == nil {
		items = []models.EquipmentCatalogItem{}
	}
	c.JSON(http.StatusOK, items)
}
