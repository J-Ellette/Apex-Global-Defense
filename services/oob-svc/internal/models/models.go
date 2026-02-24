package models

import (
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
)

// ClassificationLevel represents the data classification ceiling.
type ClassificationLevel int

const (
	UNCLASS    ClassificationLevel = 0
	FOUO       ClassificationLevel = 1
	SECRET     ClassificationLevel = 2
	TOP_SECRET ClassificationLevel = 3
	TS_SCI     ClassificationLevel = 4
)

func (c ClassificationLevel) String() string {
	switch c {
	case UNCLASS:
		return "UNCLASS"
	case FOUO:
		return "FOUO"
	case SECRET:
		return "SECRET"
	case TOP_SECRET:
		return "TOP_SECRET"
	case TS_SCI:
		return "TS_SCI"
	default:
		return "UNCLASS"
	}
}

// Role represents an RBAC role.
type Role string

const (
	RoleViewer               Role = "viewer"
	RoleAnalyst              Role = "analyst"
	RolePlanner              Role = "planner"
	RoleCommander            Role = "commander"
	RoleSimOperator          Role = "sim_operator"
	RoleAdmin                Role = "admin"
	RoleClassificationOfficer Role = "classification_officer"
)

// Permission represents a fine-grained permission.
type Permission string

const (
	PermReadOOB      Permission = "oob:read"
	PermWriteOOB     Permission = "oob:write"
	PermReadScenario  Permission = "scenario:read"
	PermWriteScenario Permission = "scenario:write"
)

// Claims is the JWT payload (must match auth-svc structure).
type Claims struct {
	UserID         string              `json:"uid"`
	Roles          []Role              `json:"roles"`
	Permissions    []Permission        `json:"perms"`
	Classification ClassificationLevel `json:"cls"`
	OrgID          string              `json:"org_id"`
	jwt.RegisteredClaims
}

// Country represents a row in the countries table.
type Country struct {
	Code             string    `db:"code"               json:"code"`
	Name             string    `db:"name"               json:"name"`
	Region           *string   `db:"region"             json:"region,omitempty"`
	AllianceCodes    []string  `db:"-"                  json:"alliance_codes"`
	GDPUsd           *int64    `db:"gdp_usd"            json:"gdp_usd,omitempty"`
	DefenseBudgetUsd *int64    `db:"defense_budget_usd" json:"defense_budget_usd,omitempty"`
	Population       *int64    `db:"population"         json:"population,omitempty"`
	AreaKm2          *int64    `db:"area_km2"           json:"area_km2,omitempty"`
	ISO2             *string   `db:"iso2"               json:"iso2,omitempty"`
	FlagEmoji        *string   `db:"flag_emoji"         json:"flag_emoji,omitempty"`
	UpdatedAt        time.Time `db:"updated_at"         json:"updated_at"`
}

// MilitaryUnit represents a row in the military_units table.
type MilitaryUnit struct {
	ID             uuid.UUID           `db:"id"             json:"id"`
	CountryCode    string              `db:"country_code"   json:"country_code"`
	Branch         string              `db:"branch"         json:"branch"`
	Echelon        *string             `db:"echelon"        json:"echelon,omitempty"`
	Name           string              `db:"name"           json:"name"`
	ShortName      *string             `db:"short_name"     json:"short_name,omitempty"`
	NATOSymbol     *string             `db:"nato_symbol"    json:"nato_symbol,omitempty"`
	ParentID       *uuid.UUID          `db:"parent_id"      json:"parent_id,omitempty"`
	Latitude       *float64            `db:"-"              json:"lat,omitempty"`
	Longitude      *float64            `db:"-"              json:"lng,omitempty"`
	Classification string              `db:"classification" json:"classification"`
	Confidence     *float64            `db:"confidence"     json:"confidence,omitempty"`
	DataSources    []string            `db:"-"              json:"data_sources,omitempty"`
	AsOf           time.Time           `db:"as_of"          json:"as_of"`
	CreatedAt      time.Time           `db:"created_at"     json:"created_at"`
	UpdatedAt      time.Time           `db:"updated_at"     json:"updated_at"`
}

// CreateUnitRequest is the body for POST /oob/units.
type CreateUnitRequest struct {
	CountryCode    string     `json:"country_code"             binding:"required,len=3"`
	Branch         string     `json:"branch"                   binding:"required"`
	Echelon        *string    `json:"echelon"`
	Name           string     `json:"name"                     binding:"required"`
	ShortName      *string    `json:"short_name"`
	NATOSymbol     *string    `json:"nato_symbol"`
	ParentID       *uuid.UUID `json:"parent_id"`
	Latitude       *float64   `json:"lat"`
	Longitude      *float64   `json:"lng"`
	Classification string     `json:"classification"`
	Confidence     *float64   `json:"confidence"`
	DataSources    []string   `json:"data_sources"`
	AsOf           time.Time  `json:"as_of"                    binding:"required"`
}

// UpdateUnitRequest is the body for PUT /oob/units/:id.
type UpdateUnitRequest struct {
	Branch         *string    `json:"branch"`
	Echelon        *string    `json:"echelon"`
	Name           *string    `json:"name"`
	ShortName      *string    `json:"short_name"`
	NATOSymbol     *string    `json:"nato_symbol"`
	ParentID       *uuid.UUID `json:"parent_id"`
	Latitude       *float64   `json:"lat"`
	Longitude      *float64   `json:"lng"`
	Classification *string    `json:"classification"`
	Confidence     *float64   `json:"confidence"`
	DataSources    []string   `json:"data_sources"`
	AsOf           *time.Time `json:"as_of"`
}

// CompareRequest is the body for POST /oob/compare.
type CompareRequest struct {
	CountryA string     `json:"country_a" binding:"required,len=3"`
	CountryB string     `json:"country_b" binding:"required,len=3"`
	AsOf     *time.Time `json:"as_of"`
}

// CountryStrength aggregates military strength metrics for a country.
type CountryStrength struct {
	Country     Country           `json:"country"`
	TotalUnits  int               `json:"total_units"`
	ByBranch    map[string]int    `json:"by_branch"`
	Personnel   *PersonnelSummary `json:"personnel,omitempty"`
}

// PersonnelSummary aggregates personnel counts.
type PersonnelSummary struct {
	Total       *int `json:"total,omitempty"`
	ActiveDuty  *int `json:"active_duty,omitempty"`
	Reserve     *int `json:"reserve,omitempty"`
	Paramilitary *int `json:"paramilitary,omitempty"`
}

// CompareResponse is returned by POST /oob/compare.
type CompareResponse struct {
	CountryA CountryStrength `json:"country_a"`
	CountryB CountryStrength `json:"country_b"`
}

// Scenario represents a named planning scenario.
type Scenario struct {
	ID             uuid.UUID  `db:"id"             json:"id"`
	Name           string     `db:"name"           json:"name"`
	Description    *string    `db:"description"    json:"description,omitempty"`
	Classification string     `db:"classification" json:"classification"`
	CreatedBy      uuid.UUID  `db:"created_by"     json:"created_by"`
	OrgID          uuid.UUID  `db:"org_id"         json:"org_id"`
	ParentID       *uuid.UUID `db:"parent_id"      json:"parent_id,omitempty"`
	Tags           []string   `db:"-"              json:"tags"`
	CreatedAt      time.Time  `db:"created_at"     json:"created_at"`
	UpdatedAt      time.Time  `db:"updated_at"     json:"updated_at"`
}

// CreateScenarioRequest is the body for POST /scenarios.
type CreateScenarioRequest struct {
	Name           string   `json:"name"           binding:"required"`
	Description    *string  `json:"description"`
	Classification string   `json:"classification"`
	Tags           []string `json:"tags"`
}

// UpdateScenarioRequest is the body for PUT /scenarios/:id.
type UpdateScenarioRequest struct {
	Name           *string  `json:"name"`
	Description    *string  `json:"description"`
	Classification *string  `json:"classification"`
	Tags           []string `json:"tags"`
}

// EquipmentCatalogItem represents a row in the equipment_catalog table.
type EquipmentCatalogItem struct {
	TypeCode      string    `db:"type_code"       json:"type_code"`
	Category      string    `db:"category"        json:"category"`
	Name          string    `db:"name"            json:"name"`
	OriginCountry *string   `db:"origin_country"  json:"origin_country,omitempty"`
	Specs         *[]byte   `db:"specs"           json:"specs,omitempty"`
	ThreatScore   *float64  `db:"threat_score"    json:"threat_score,omitempty"`
	InServiceYear *int      `db:"in_service_year" json:"in_service_year,omitempty"`
	UpdatedAt     time.Time `db:"updated_at"      json:"updated_at"`
}
