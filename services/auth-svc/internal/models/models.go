package models

import (
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
)

// ClassificationLevel represents the data classification ceiling for a user or record.
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

// Scan implements sql.Scanner so PostgreSQL ENUM strings map to ClassificationLevel ints.
func (c *ClassificationLevel) Scan(src interface{}) error {
	var s string
	switch v := src.(type) {
	case string:
		s = v
	case []byte:
		s = string(v)
	default:
		return fmt.Errorf("ClassificationLevel.Scan: unsupported type %T", src)
	}
	switch s {
	case "UNCLASS":
		*c = UNCLASS
	case "FOUO":
		*c = FOUO
	case "SECRET":
		*c = SECRET
	case "TOP_SECRET":
		*c = TOP_SECRET
	case "TS_SCI":
		*c = TS_SCI
	default:
		return fmt.Errorf("ClassificationLevel.Scan: unknown value %q", s)
	}
	return nil
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
	PermReadScenario    Permission = "scenario:read"
	PermWriteScenario   Permission = "scenario:write"
	PermReadOOB         Permission = "oob:read"
	PermWriteOOB        Permission = "oob:write"
	PermReadIntel       Permission = "intel:read"
	PermWriteIntel      Permission = "intel:write"
	PermRunSimulation   Permission = "simulation:run"
	PermControlSim      Permission = "simulation:control"
	PermManageUsers     Permission = "users:manage"
	PermManageClassification Permission = "classification:manage"
	PermMapControl      Permission = "map:control"
)

// RolePermissions maps roles to their default permissions.
var RolePermissions = map[Role][]Permission{
	RoleViewer:    {PermReadScenario, PermReadOOB},
	RoleAnalyst:   {PermReadScenario, PermReadOOB, PermReadIntel, PermWriteIntel},
	RolePlanner:   {PermReadScenario, PermWriteScenario, PermReadOOB, PermWriteOOB, PermReadIntel, PermMapControl},
	RoleCommander: {PermReadScenario, PermWriteScenario, PermReadOOB, PermWriteOOB, PermReadIntel, PermWriteIntel, PermMapControl},
	RoleSimOperator: {
		PermReadScenario, PermReadOOB, PermRunSimulation, PermControlSim, PermMapControl,
	},
	RoleAdmin: {
		PermReadScenario, PermWriteScenario, PermReadOOB, PermWriteOOB,
		PermReadIntel, PermWriteIntel, PermRunSimulation, PermControlSim,
		PermManageUsers, PermMapControl,
	},
	RoleClassificationOfficer: {PermManageClassification},
}

// Claims is the JWT payload for AGD tokens.
type Claims struct {
	UserID         string              `json:"uid"`
	Roles          []Role              `json:"roles"`
	Permissions    []Permission        `json:"perms"`
	Classification ClassificationLevel `json:"cls"`
	OrgID          string              `json:"org_id"`
	jwt.RegisteredClaims
}

// User represents a user record from the database.
type User struct {
	ID             uuid.UUID           `db:"id"              json:"id"`
	Email          string              `db:"email"           json:"email"`
	DisplayName    string              `db:"display_name"    json:"display_name"`
	Roles          []Role              `db:"roles"           json:"roles"`
	Classification ClassificationLevel `db:"classification"  json:"classification"`
	OrgID          uuid.UUID           `db:"org_id"          json:"org_id"`
	Active         bool                `db:"active"          json:"active"`
	CreatedAt      time.Time           `db:"created_at"      json:"created_at"`
	LastLoginAt    *time.Time          `db:"last_login_at"   json:"last_login_at,omitempty"`
}

// LoginRequest is the body for POST /auth/login.
type LoginRequest struct {
	Email    string `json:"email"    binding:"required,email"`
	Password string `json:"password" binding:"required,min=8"`
}

// LoginResponse is returned on successful authentication.
type LoginResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	TokenType    string `json:"token_type"`
	ExpiresIn    int    `json:"expires_in"`
	User         User   `json:"user"`
}

// RefreshRequest is the body for POST /auth/refresh.
type RefreshRequest struct {
	RefreshToken string `json:"refresh_token" binding:"required"`
}
