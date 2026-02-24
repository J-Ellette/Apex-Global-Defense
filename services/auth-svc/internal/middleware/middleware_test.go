package middleware_test

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	"github.com/j-ellette/apex-global-defense/services/auth-svc/internal/middleware"
	"github.com/j-ellette/apex-global-defense/services/auth-svc/internal/models"
)

const secret = "test-secret-must-be-at-least-32-characters"

func makeToken(t *testing.T, claims *models.Claims) string {
	t.Helper()
	tok := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	signed, err := tok.SignedString([]byte(secret))
	if err != nil {
		t.Fatalf("sign token: %v", err)
	}
	return signed
}

func testClaims(roles []models.Role, cls models.ClassificationLevel) *models.Claims {
	return &models.Claims{
		UserID:         uuid.New().String(),
		Roles:          roles,
		Permissions:    []models.Permission{},
		Classification: cls,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(time.Hour)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	}
}


// ── JWTAuth ───────────────────────────────────────────────────────────────────

func TestJWTAuth_ValidToken_Passes(t *testing.T) {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.GET("/protected", middleware.JWTAuth(secret), func(c *gin.Context) {
		c.Status(http.StatusOK)
	})

	claims := testClaims([]models.Role{models.RoleAnalyst}, models.FOUO)
	tok := makeToken(t, claims)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/protected", nil)
	req.Header.Set("Authorization", "Bearer "+tok)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}
}

func TestJWTAuth_MissingHeader_Returns401(t *testing.T) {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.GET("/protected", middleware.JWTAuth(secret), func(c *gin.Context) {
		c.Status(http.StatusOK)
	})

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/protected", nil)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401, got %d", w.Code)
	}
}

func TestJWTAuth_ExpiredToken_Returns401(t *testing.T) {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.GET("/protected", middleware.JWTAuth(secret), func(c *gin.Context) {
		c.Status(http.StatusOK)
	})

	claims := testClaims([]models.Role{models.RoleAnalyst}, models.FOUO)
	claims.ExpiresAt = jwt.NewNumericDate(time.Now().Add(-time.Hour))
	tok := makeToken(t, claims)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/protected", nil)
	req.Header.Set("Authorization", "Bearer "+tok)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401, got %d", w.Code)
	}
}

// ── RequireRole ───────────────────────────────────────────────────────────────

func TestRequireRole_UserHasRole_Passes(t *testing.T) {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.GET("/admin",
		middleware.JWTAuth(secret),
		middleware.RequireRole(models.RoleAdmin),
		func(c *gin.Context) { c.Status(http.StatusOK) },
	)

	claims := testClaims([]models.Role{models.RoleAdmin}, models.TOP_SECRET)
	tok := makeToken(t, claims)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/admin", nil)
	req.Header.Set("Authorization", "Bearer "+tok)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}
}

func TestRequireRole_UserLacksRole_Returns403(t *testing.T) {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.GET("/admin",
		middleware.JWTAuth(secret),
		middleware.RequireRole(models.RoleAdmin),
		func(c *gin.Context) { c.Status(http.StatusOK) },
	)

	claims := testClaims([]models.Role{models.RoleViewer}, models.UNCLASS)
	tok := makeToken(t, claims)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/admin", nil)
	req.Header.Set("Authorization", "Bearer "+tok)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusForbidden {
		t.Fatalf("expected 403, got %d", w.Code)
	}
}

// ── ClassificationGate ────────────────────────────────────────────────────────

func TestClassificationGate_SufficientLevel_Passes(t *testing.T) {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.GET("/secret",
		middleware.JWTAuth(secret),
		middleware.ClassificationGate(models.SECRET),
		func(c *gin.Context) { c.Status(http.StatusOK) },
	)

	claims := testClaims([]models.Role{models.RoleAnalyst}, models.TOP_SECRET)
	tok := makeToken(t, claims)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/secret", nil)
	req.Header.Set("Authorization", "Bearer "+tok)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", w.Code)
	}
}

func TestClassificationGate_InsufficientLevel_Returns403(t *testing.T) {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.GET("/secret",
		middleware.JWTAuth(secret),
		middleware.ClassificationGate(models.SECRET),
		func(c *gin.Context) { c.Status(http.StatusOK) },
	)

	claims := testClaims([]models.Role{models.RoleViewer}, models.UNCLASS)
	tok := makeToken(t, claims)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest(http.MethodGet, "/secret", nil)
	req.Header.Set("Authorization", "Bearer "+tok)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusForbidden {
		t.Fatalf("expected 403, got %d", w.Code)
	}
}
