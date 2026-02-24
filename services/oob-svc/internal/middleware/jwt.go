package middleware

import (
	"errors"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/j-ellette/apex-global-defense/services/oob-svc/internal/models"
)

const claimsKey = "claims"

// JWTAuth validates the Bearer token in the Authorization header and stores
// the parsed Claims in the Gin context under the key "claims".
func JWTAuth(jwtSecret string) gin.HandlerFunc {
	return func(c *gin.Context) {
		header := c.GetHeader("Authorization")
		if header == "" {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "missing_authorization_header"})
			return
		}

		parts := strings.SplitN(header, " ", 2)
		if len(parts) != 2 || !strings.EqualFold(parts[0], "bearer") {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "invalid_authorization_format"})
			return
		}

		tokenStr := parts[1]
		claims := &models.Claims{}

		token, err := jwt.ParseWithClaims(tokenStr, claims, func(t *jwt.Token) (interface{}, error) {
			if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
				return nil, errors.New("unexpected signing method")
			}
			return []byte(jwtSecret), nil
		})
		if err != nil || !token.Valid {
			c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "invalid_token"})
			return
		}

		c.Set(claimsKey, claims)
		c.Next()
	}
}

// GetClaims retrieves the parsed JWT claims from the Gin context.
func GetClaims(c *gin.Context) *models.Claims {
	return c.MustGet(claimsKey).(*models.Claims)
}
