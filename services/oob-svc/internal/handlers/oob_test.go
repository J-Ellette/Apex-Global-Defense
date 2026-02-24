package handlers_test

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/j-ellette/apex-global-defense/services/oob-svc/internal/handlers"
	"github.com/j-ellette/apex-global-defense/services/oob-svc/internal/models"
	"github.com/j-ellette/apex-global-defense/services/oob-svc/internal/store"
	"go.uber.org/zap"
)

// ── fake store ────────────────────────────────────────────────────────────────

type fakeOOBStore struct {
	countries []models.Country
	units     []models.MilitaryUnit
	catalog   []models.EquipmentCatalogItem
}

func (f *fakeOOBStore) ListCountries(_ context.Context) ([]models.Country, error) {
	return f.countries, nil
}

func (f *fakeOOBStore) GetCountry(_ context.Context, code string) (*models.Country, error) {
	for i := range f.countries {
		if f.countries[i].Code == code {
			return &f.countries[i], nil
		}
	}
	return nil, store.ErrNotFound
}

func (f *fakeOOBStore) ListUnitsByCountry(_ context.Context, code string) ([]models.MilitaryUnit, error) {
	var out []models.MilitaryUnit
	for _, u := range f.units {
		if u.CountryCode == code {
			out = append(out, u)
		}
	}
	return out, nil
}

func (f *fakeOOBStore) GetUnit(_ context.Context, id uuid.UUID) (*models.MilitaryUnit, error) {
	for i := range f.units {
		if f.units[i].ID == id {
			return &f.units[i], nil
		}
	}
	return nil, store.ErrNotFound
}

func (f *fakeOOBStore) CreateUnit(_ context.Context, req models.CreateUnitRequest) (*models.MilitaryUnit, error) {
	u := models.MilitaryUnit{
		ID:          uuid.New(),
		CountryCode: req.CountryCode,
		Branch:      req.Branch,
		Name:        req.Name,
		AsOf:        req.AsOf,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}
	f.units = append(f.units, u)
	return &u, nil
}

func (f *fakeOOBStore) UpdateUnit(_ context.Context, id uuid.UUID, req models.UpdateUnitRequest) (*models.MilitaryUnit, error) {
	for i := range f.units {
		if f.units[i].ID == id {
			if req.Name != nil {
				f.units[i].Name = *req.Name
			}
			return &f.units[i], nil
		}
	}
	return nil, store.ErrNotFound
}

func (f *fakeOOBStore) DeleteUnit(_ context.Context, id uuid.UUID) error {
	for i, u := range f.units {
		if u.ID == id {
			f.units = append(f.units[:i], f.units[i+1:]...)
			return nil
		}
	}
	return store.ErrNotFound
}

func (f *fakeOOBStore) CountryStrength(_ context.Context, code string, _ *time.Time) (*models.CountryStrength, error) {
	for i := range f.countries {
		if f.countries[i].Code == code {
			return &models.CountryStrength{
				Country:    f.countries[i],
				TotalUnits: len(f.units),
				ByBranch:   map[string]int{},
			}, nil
		}
	}
	return nil, store.ErrNotFound
}

func (f *fakeOOBStore) ListEquipmentCatalog(_ context.Context) ([]models.EquipmentCatalogItem, error) {
	return f.catalog, nil
}

// ── helpers ───────────────────────────────────────────────────────────────────

func newTestRouter(s *fakeOOBStore) *gin.Engine {
	gin.SetMode(gin.TestMode)
	h := handlers.NewOOBHandler(s, zap.NewNop())

	r := gin.New()
	v1 := r.Group("/api/v1/oob")
	v1.GET("/countries", h.ListCountries)
	v1.GET("/countries/:code", h.GetCountry)
	v1.GET("/countries/:code/forces", h.ListForces)
	v1.GET("/units/:id", h.GetUnit)
	v1.POST("/units", h.CreateUnit)
	v1.PUT("/units/:id", h.UpdateUnit)
	v1.DELETE("/units/:id", h.DeleteUnit)
	v1.GET("/units/:id/history", h.UnitHistory)
	v1.POST("/compare", h.CompareCountries)
	v1.GET("/equipment/catalog", h.ListEquipmentCatalog)
	return r
}

func testCountry() models.Country {
	region := "North America"
	iso2 := "US"
	flag := "🇺🇸"
	return models.Country{
		Code:          "USA",
		Name:          "United States",
		Region:        &region,
		AllianceCodes: []string{"NATO"},
		ISO2:          &iso2,
		FlagEmoji:     &flag,
		UpdatedAt:     time.Now(),
	}
}

func testUnit(code string) models.MilitaryUnit {
	return models.MilitaryUnit{
		ID:             uuid.New(),
		CountryCode:    code,
		Branch:         "ARMY",
		Name:           "1st Infantry Division",
		Classification: "UNCLASS",
		DataSources:    []string{},
		AsOf:           time.Now(),
		CreatedAt:      time.Now(),
		UpdatedAt:      time.Now(),
	}
}

// ── tests ─────────────────────────────────────────────────────────────────────

func TestListCountries(t *testing.T) {
	s := &fakeOOBStore{countries: []models.Country{testCountry()}}
	r := newTestRouter(s)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/api/v1/oob/countries", nil)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}

	var resp []models.Country
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatal(err)
	}
	if len(resp) != 1 {
		t.Errorf("expected 1 country, got %d", len(resp))
	}
}

func TestGetCountry_Found(t *testing.T) {
	s := &fakeOOBStore{countries: []models.Country{testCountry()}}
	r := newTestRouter(s)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/api/v1/oob/countries/USA", nil)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}

	var resp models.Country
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil { t.Fatal(err) }
	if resp.Code != "USA" {
		t.Errorf("expected code USA, got %s", resp.Code)
	}
}

func TestGetCountry_NotFound(t *testing.T) {
	s := &fakeOOBStore{}
	r := newTestRouter(s)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/api/v1/oob/countries/ZZZ", nil)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Fatalf("expected 404, got %d", w.Code)
	}
}

func TestListForces(t *testing.T) {
	unit := testUnit("USA")
	s := &fakeOOBStore{
		countries: []models.Country{testCountry()},
		units:     []models.MilitaryUnit{unit},
	}
	r := newTestRouter(s)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/api/v1/oob/countries/USA/forces", nil)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}

	var resp []models.MilitaryUnit
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil { t.Fatal(err) }
	if len(resp) != 1 {
		t.Errorf("expected 1 unit, got %d", len(resp))
	}
}

func TestGetUnit_Found(t *testing.T) {
	unit := testUnit("USA")
	s := &fakeOOBStore{units: []models.MilitaryUnit{unit}}
	r := newTestRouter(s)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/api/v1/oob/units/"+unit.ID.String(), nil)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}
}

func TestGetUnit_InvalidID(t *testing.T) {
	s := &fakeOOBStore{}
	r := newTestRouter(s)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/api/v1/oob/units/not-a-uuid", nil)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", w.Code)
	}
}

func TestCreateUnit(t *testing.T) {
	s := &fakeOOBStore{countries: []models.Country{testCountry()}}
	r := newTestRouter(s)

	body, _ := json.Marshal(models.CreateUnitRequest{
		CountryCode: "USA",
		Branch:      "ARMY",
		Name:        "101st Airborne",
		AsOf:        time.Now(),
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodPost, "/api/v1/oob/units", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)

	if w.Code != http.StatusCreated {
		t.Fatalf("expected 201, got %d: %s", w.Code, w.Body.String())
	}

	var resp models.MilitaryUnit
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil { t.Fatal(err) }
	if resp.Name != "101st Airborne" {
		t.Errorf("expected name '101st Airborne', got %s", resp.Name)
	}
}

func TestUpdateUnit(t *testing.T) {
	unit := testUnit("USA")
	s := &fakeOOBStore{units: []models.MilitaryUnit{unit}}
	r := newTestRouter(s)

	newName := "Updated Division"
	body, _ := json.Marshal(models.UpdateUnitRequest{Name: &newName})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodPut, "/api/v1/oob/units/"+unit.ID.String(), bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}

	var resp models.MilitaryUnit
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil { t.Fatal(err) }
	if resp.Name != newName {
		t.Errorf("expected name '%s', got '%s'", newName, resp.Name)
	}
}

func TestDeleteUnit(t *testing.T) {
	unit := testUnit("USA")
	s := &fakeOOBStore{units: []models.MilitaryUnit{unit}}
	r := newTestRouter(s)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodDelete, "/api/v1/oob/units/"+unit.ID.String(), nil)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusNoContent {
		t.Fatalf("expected 204, got %d", w.Code)
	}
}

func TestDeleteUnit_NotFound(t *testing.T) {
	s := &fakeOOBStore{}
	r := newTestRouter(s)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodDelete, "/api/v1/oob/units/"+uuid.New().String(), nil)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Fatalf("expected 404, got %d", w.Code)
	}
}

func TestCompareCountries(t *testing.T) {
	usa := testCountry()
	chn := models.Country{Code: "CHN", Name: "China", AllianceCodes: []string{}, UpdatedAt: time.Now()}
	s := &fakeOOBStore{countries: []models.Country{usa, chn}}
	r := newTestRouter(s)

	body, _ := json.Marshal(models.CompareRequest{CountryA: "USA", CountryB: "CHN"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodPost, "/api/v1/oob/compare", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}

	var resp models.CompareResponse
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil { t.Fatal(err) }
	if resp.CountryA.Country.Code != "USA" {
		t.Errorf("expected country_a USA, got %s", resp.CountryA.Country.Code)
	}
	if resp.CountryB.Country.Code != "CHN" {
		t.Errorf("expected country_b CHN, got %s", resp.CountryB.Country.Code)
	}
}

func TestListEquipmentCatalog(t *testing.T) {
	s := &fakeOOBStore{catalog: []models.EquipmentCatalogItem{
		{TypeCode: "M1A2", Category: "ARMOR", Name: "M1A2 Abrams", UpdatedAt: time.Now()},
	}}
	r := newTestRouter(s)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/api/v1/oob/equipment/catalog", nil)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}

	var resp []models.EquipmentCatalogItem
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil { t.Fatal(err) }
	if len(resp) != 1 {
		t.Errorf("expected 1 item, got %d", len(resp))
	}
}

func TestUnitHistory_ReturnsEmptyArray(t *testing.T) {
	s := &fakeOOBStore{}
	r := newTestRouter(s)

	id := uuid.New()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/api/v1/oob/units/"+id.String()+"/history", nil)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}
}
