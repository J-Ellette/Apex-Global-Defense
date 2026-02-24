package store

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
	"github.com/j-ellette/apex-global-defense/services/auth-svc/internal/models"
)

// UserStore manages user persistence in PostgreSQL.
type UserStore struct {
	db *sqlx.DB
}

// NewUserStore creates a new UserStore using the provided database connection.
func NewUserStore(db *sqlx.DB) *UserStore {
	return &UserStore{db: db}
}

// GetByEmail retrieves a user by email address.
func (s *UserStore) GetByEmail(ctx context.Context, email string) (*models.User, error) {
	const q = `
		SELECT id, email, display_name, roles, classification, org_id, active, created_at, last_login_at
		FROM users
		WHERE email = $1 AND active = true`

	row := s.db.QueryRowContext(ctx, q, email)
	return scanUser(row)
}

// GetByID retrieves a user by UUID.
func (s *UserStore) GetByID(ctx context.Context, id uuid.UUID) (*models.User, error) {
	const q = `
		SELECT id, email, display_name, roles, classification, org_id, active, created_at, last_login_at
		FROM users
		WHERE id = $1 AND active = true`

	row := s.db.QueryRowContext(ctx, q, id)
	return scanUser(row)
}

// UpdateLastLogin sets the last_login_at timestamp for a user.
func (s *UserStore) UpdateLastLogin(ctx context.Context, id uuid.UUID) error {
	_, err := s.db.ExecContext(ctx,
		`UPDATE users SET last_login_at = NOW() WHERE id = $1`, id)
	return err
}

func scanUser(row *sql.Row) (*models.User, error) {
	u := &models.User{}
	var rolesJSON []byte
	var lastLogin sql.NullTime

	err := row.Scan(
		&u.ID, &u.Email, &u.DisplayName, &rolesJSON,
		&u.Classification, &u.OrgID, &u.Active, &u.CreatedAt, &lastLogin,
	)
	if err != nil {
		return nil, fmt.Errorf("scan user: %w", err)
	}

	if err := json.Unmarshal(rolesJSON, &u.Roles); err != nil {
		return nil, fmt.Errorf("unmarshal roles: %w", err)
	}

	if lastLogin.Valid {
		t := lastLogin.Time
		u.LastLoginAt = &t
	}

	return u, nil
}

// SessionStore manages refresh token sessions in Redis.
type SessionStore struct {
	rdb interface {
		Set(ctx context.Context, key string, value interface{}, expiration time.Duration) error
		Get(ctx context.Context, key string) (string, error)
		Del(ctx context.Context, keys ...string) error
	}
}

// NewSessionStore creates a new SessionStore backed by Redis.
func NewSessionStore(rdb interface {
	Set(ctx context.Context, key string, value interface{}, expiration time.Duration) error
	Get(ctx context.Context, key string) (string, error)
	Del(ctx context.Context, keys ...string) error
}) *SessionStore {
	return &SessionStore{rdb: rdb}
}

// SaveRefreshToken stores a refresh token with the given TTL.
func (s *SessionStore) SaveRefreshToken(ctx context.Context, token string, userID uuid.UUID, ttl time.Duration) error {
	key := fmt.Sprintf("session:%s", token)
	return s.rdb.Set(ctx, key, userID.String(), ttl)
}

// ValidateRefreshToken retrieves the user ID associated with a refresh token.
// Returns an error if the token does not exist or has expired.
func (s *SessionStore) ValidateRefreshToken(ctx context.Context, token string) (uuid.UUID, error) {
	key := fmt.Sprintf("session:%s", token)
	val, err := s.rdb.Get(ctx, key)
	if err != nil {
		return uuid.Nil, fmt.Errorf("refresh token not found or expired")
	}
	return uuid.Parse(val)
}

// DeleteRefreshToken removes a refresh token (logout).
func (s *SessionStore) DeleteRefreshToken(ctx context.Context, token string) error {
	key := fmt.Sprintf("session:%s", token)
	return s.rdb.Del(ctx, key)
}
