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
	"github.com/j-ellette/apex-global-defense/services/auth-svc/internal/handlers"
	"github.com/j-ellette/apex-global-defense/services/auth-svc/internal/models"
	"go.uber.org/zap"
)

const testSecret = "test-secret-at-least-32-bytes-long-ok"

// --- fakes ---

type fakeUserStore struct {
	user *models.User
}

func (f *fakeUserStore) GetByEmail(_ context.Context, email string) (*models.User, error) {
	if f.user != nil && f.user.Email == email {
		return f.user, nil
	}
	return nil, errNotFound
}

func (f *fakeUserStore) GetByID(_ context.Context, id uuid.UUID) (*models.User, error) {
	if f.user != nil && f.user.ID == id {
		return f.user, nil
	}
	return nil, errNotFound
}

func (f *fakeUserStore) UpdateLastLogin(_ context.Context, _ uuid.UUID) error { return nil }

func (f *fakeUserStore) WriteAuditLogAsync(_, _, _ string, _ uuid.UUID, _ interface{}) {}

type fakeSessionStore struct {
	tokens map[string]uuid.UUID
}

func newFakeSessionStore() *fakeSessionStore {
	return &fakeSessionStore{tokens: make(map[string]uuid.UUID)}
}

func (f *fakeSessionStore) SaveRefreshToken(_ context.Context, token string, userID uuid.UUID, _ time.Duration) error {
	f.tokens[token] = userID
	return nil
}

func (f *fakeSessionStore) ValidateRefreshToken(_ context.Context, token string) (uuid.UUID, error) {
	if id, ok := f.tokens[token]; ok {
		return id, nil
	}
	return uuid.Nil, errNotFound
}

func (f *fakeSessionStore) DeleteRefreshToken(_ context.Context, token string) error {
	delete(f.tokens, token)
	return nil
}

type errType string

func (e errType) Error() string { return string(e) }

const errNotFound = errType("not found")

// --- helpers ---

func newRouter(users *fakeUserStore, sessions *fakeSessionStore) *gin.Engine {
	gin.SetMode(gin.TestMode)
	h := handlers.NewAuthHandler(
		users,
		sessions,
		testSecret,
		"agd-test",
		15*time.Minute,
		8*time.Hour,
		zap.NewNop(),
	)

	r := gin.New()
	r.POST("/api/v1/auth/login", h.Login)
	r.POST("/api/v1/auth/refresh", h.Refresh)
	r.POST("/api/v1/auth/logout", h.Logout)
	return r
}

func testUser() *models.User {
	return &models.User{
		ID:             uuid.New(),
		Email:          "analyst@agd.test",
		DisplayName:    "Test Analyst",
		Roles:          []models.Role{models.RoleAnalyst},
		Classification: models.FOUO,
		OrgID:          uuid.New(),
		Active:         true,
	}
}

// --- tests ---

func TestLogin_Success(t *testing.T) {
	user := testUser()
	r := newRouter(&fakeUserStore{user: user}, newFakeSessionStore())

	body, _ := json.Marshal(models.LoginRequest{Email: user.Email, Password: "password123"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodPost, "/api/v1/auth/login", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}

	var resp models.LoginResponse
	if err := json.Unmarshal(w.Body.Bytes(), &resp); err != nil {
		t.Fatal(err)
	}
	if resp.AccessToken == "" {
		t.Error("expected non-empty access token")
	}
	if resp.RefreshToken == "" {
		t.Error("expected non-empty refresh token")
	}
	if resp.TokenType != "Bearer" {
		t.Errorf("expected token type Bearer, got %s", resp.TokenType)
	}
}

func TestLogin_UnknownEmail_Returns401(t *testing.T) {
	r := newRouter(&fakeUserStore{}, newFakeSessionStore())

	body, _ := json.Marshal(models.LoginRequest{Email: "unknown@agd.test", Password: "password123"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodPost, "/api/v1/auth/login", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)

	if w.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401, got %d", w.Code)
	}
}

func TestRefresh_ValidToken(t *testing.T) {
	user := testUser()
	sessions := newFakeSessionStore()
	r := newRouter(&fakeUserStore{user: user}, sessions)

	// First, log in to get a refresh token.
	body, _ := json.Marshal(models.LoginRequest{Email: user.Email, Password: "password123"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodPost, "/api/v1/auth/login", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)

	var loginResp models.LoginResponse
	json.Unmarshal(w.Body.Bytes(), &loginResp) //nolint:errcheck

	// Now refresh.
	body, _ = json.Marshal(models.RefreshRequest{RefreshToken: loginResp.RefreshToken})
	w = httptest.NewRecorder()
	req, _ = http.NewRequest(http.MethodPost, "/api/v1/auth/refresh", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
}

func TestRefresh_InvalidToken_Returns401(t *testing.T) {
	user := testUser()
	r := newRouter(&fakeUserStore{user: user}, newFakeSessionStore())

	body, _ := json.Marshal(models.RefreshRequest{RefreshToken: "invalid-token"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodPost, "/api/v1/auth/refresh", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)

	if w.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401, got %d", w.Code)
	}
}

func TestLogout_DeletesSession(t *testing.T) {
	user := testUser()
	sessions := newFakeSessionStore()
	r := newRouter(&fakeUserStore{user: user}, sessions)

	// Log in.
	body, _ := json.Marshal(models.LoginRequest{Email: user.Email, Password: "password123"})
	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodPost, "/api/v1/auth/login", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)

	var loginResp models.LoginResponse
	json.Unmarshal(w.Body.Bytes(), &loginResp) //nolint:errcheck

	// Log out.
	body, _ = json.Marshal(models.RefreshRequest{RefreshToken: loginResp.RefreshToken})
	w = httptest.NewRecorder()
	req, _ = http.NewRequest(http.MethodPost, "/api/v1/auth/logout", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)

	if w.Code != http.StatusNoContent {
		t.Fatalf("expected 204, got %d", w.Code)
	}

	// Refresh should now fail.
	body, _ = json.Marshal(models.RefreshRequest{RefreshToken: loginResp.RefreshToken})
	w = httptest.NewRecorder()
	req, _ = http.NewRequest(http.MethodPost, "/api/v1/auth/refresh", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)

	if w.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401 after logout, got %d", w.Code)
	}
}
