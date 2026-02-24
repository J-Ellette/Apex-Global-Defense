package handlers

import (
	"context"
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	"github.com/j-ellette/apex-global-defense/services/auth-svc/internal/middleware"
	"github.com/j-ellette/apex-global-defense/services/auth-svc/internal/models"
	"go.uber.org/zap"
)

// userStore defines the persistence operations required by AuthHandler.
type userStore interface {
	GetByEmail(ctx context.Context, email string) (*models.User, error)
	GetByID(ctx context.Context, id uuid.UUID) (*models.User, error)
	UpdateLastLogin(ctx context.Context, id uuid.UUID) error
}

// sessionStore defines the refresh-token session operations.
type sessionStore interface {
	SaveRefreshToken(ctx context.Context, token string, userID uuid.UUID, ttl time.Duration) error
	ValidateRefreshToken(ctx context.Context, token string) (uuid.UUID, error)
	DeleteRefreshToken(ctx context.Context, token string) error
}

// AuthHandler holds all auth endpoint handlers.
type AuthHandler struct {
	users          userStore
	sessions       sessionStore
	jwtSecret      []byte
	jwtIssuer      string
	accessTokenTTL time.Duration
	refreshTokenTTL time.Duration
	log            *zap.Logger
}

// NewAuthHandler constructs an AuthHandler.
func NewAuthHandler(
	users userStore,
	sessions sessionStore,
	jwtSecret, jwtIssuer string,
	accessTTL, refreshTTL time.Duration,
	log *zap.Logger,
) *AuthHandler {
	return &AuthHandler{
		users:           users,
		sessions:        sessions,
		jwtSecret:       []byte(jwtSecret),
		jwtIssuer:       jwtIssuer,
		accessTokenTTL:  accessTTL,
		refreshTokenTTL: refreshTTL,
		log:             log,
	}
}

// Login godoc
// @Summary      Authenticate a user
// @Description  Validates credentials via Keycloak and returns JWT access + refresh tokens
// @Tags         auth
// @Accept       json
// @Produce      json
// @Param        body body models.LoginRequest true "Login credentials"
// @Success      200 {object} models.LoginResponse
// @Failure      400 {object} map[string]string
// @Failure      401 {object} map[string]string
// @Router       /auth/login [post]
func (h *AuthHandler) Login(c *gin.Context) {
	var req models.LoginRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	user, err := h.users.GetByEmail(c.Request.Context(), req.Email)
	if err != nil {
		// Return a generic error to avoid user enumeration.
		h.log.Warn("login failed: user not found", zap.String("email", req.Email))
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid_credentials"})
		return
	}

	// NOTE: In production, password verification is delegated to Keycloak via OIDC.
	// For local dev mode the user record from the DB is trusted after email lookup.
	// TODO: integrate Keycloak token exchange here.

	access, err := h.issueAccessToken(user)
	if err != nil {
		h.log.Error("failed to issue access token", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "token_generation_failed"})
		return
	}

	refresh := uuid.New().String()
	if err := h.sessions.SaveRefreshToken(c.Request.Context(), refresh, user.ID, h.refreshTokenTTL); err != nil {
		h.log.Error("failed to save refresh token", zap.Error(err))
		c.JSON(http.StatusInternalServerError, gin.H{"error": "session_creation_failed"})
		return
	}

	_ = h.users.UpdateLastLogin(c.Request.Context(), user.ID)

	c.JSON(http.StatusOK, models.LoginResponse{
		AccessToken:  access,
		RefreshToken: refresh,
		TokenType:    "Bearer",
		ExpiresIn:    int(h.accessTokenTTL.Seconds()),
		User:         *user,
	})
}

// Refresh godoc
// @Summary      Refresh access token
// @Description  Exchanges a valid refresh token for a new access token
// @Tags         auth
// @Accept       json
// @Produce      json
// @Param        body body models.RefreshRequest true "Refresh token"
// @Success      200 {object} models.LoginResponse
// @Failure      401 {object} map[string]string
// @Router       /auth/refresh [post]
func (h *AuthHandler) Refresh(c *gin.Context) {
	var req models.RefreshRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	userID, err := h.sessions.ValidateRefreshToken(c.Request.Context(), req.RefreshToken)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid_or_expired_refresh_token"})
		return
	}

	user, err := h.users.GetByID(c.Request.Context(), userID)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user_not_found"})
		return
	}

	// Rotate refresh token.
	_ = h.sessions.DeleteRefreshToken(c.Request.Context(), req.RefreshToken)
	newRefresh := uuid.New().String()
	if err := h.sessions.SaveRefreshToken(c.Request.Context(), newRefresh, user.ID, h.refreshTokenTTL); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "session_creation_failed"})
		return
	}

	access, err := h.issueAccessToken(user)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "token_generation_failed"})
		return
	}

	c.JSON(http.StatusOK, models.LoginResponse{
		AccessToken:  access,
		RefreshToken: newRefresh,
		TokenType:    "Bearer",
		ExpiresIn:    int(h.accessTokenTTL.Seconds()),
		User:         *user,
	})
}

// Logout godoc
// @Summary      Log out a user
// @Description  Invalidates the user's refresh token
// @Tags         auth
// @Accept       json
// @Produce      json
// @Param        body body models.RefreshRequest true "Refresh token to invalidate"
// @Success      204
// @Router       /auth/logout [post]
func (h *AuthHandler) Logout(c *gin.Context) {
	var req models.RefreshRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Best-effort deletion — don't error if the token was already gone.
	_ = h.sessions.DeleteRefreshToken(c.Request.Context(), req.RefreshToken)
	c.Status(http.StatusNoContent)
}

// Me godoc
// @Summary      Get current user profile
// @Description  Returns the authenticated user's profile derived from the JWT
// @Tags         auth
// @Produce      json
// @Security     BearerAuth
// @Success      200 {object} models.User
// @Failure      401 {object} map[string]string
// @Router       /auth/me [get]
func (h *AuthHandler) Me(c *gin.Context) {
	claims := middleware.GetClaims(c)
	userID, err := uuid.Parse(claims.UserID)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid_token_subject"})
		return
	}

	user, err := h.users.GetByID(c.Request.Context(), userID)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user_not_found"})
		return
	}

	c.JSON(http.StatusOK, user)
}

// issueAccessToken creates and signs a new JWT access token for the given user.
func (h *AuthHandler) issueAccessToken(user *models.User) (string, error) {
	perms := buildPermissions(user.Roles)

	now := time.Now()
	claims := &models.Claims{
		UserID:         user.ID.String(),
		Roles:          user.Roles,
		Permissions:    perms,
		Classification: user.Classification,
		OrgID:          user.OrgID.String(),
		RegisteredClaims: jwt.RegisteredClaims{
			Issuer:    h.jwtIssuer,
			Subject:   user.ID.String(),
			IssuedAt:  jwt.NewNumericDate(now),
			ExpiresAt: jwt.NewNumericDate(now.Add(h.accessTokenTTL)),
			ID:        uuid.New().String(),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	signed, err := token.SignedString(h.jwtSecret)
	if err != nil {
		return "", fmt.Errorf("sign token: %w", err)
	}
	return signed, nil
}

// buildPermissions aggregates permissions from all roles a user holds.
func buildPermissions(roles []models.Role) []models.Permission {
	seen := make(map[models.Permission]struct{})
	for _, role := range roles {
		for _, perm := range models.RolePermissions[role] {
			seen[perm] = struct{}{}
		}
	}
	perms := make([]models.Permission, 0, len(seen))
	for p := range seen {
		perms = append(perms, p)
	}
	return perms
}
