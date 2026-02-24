package middleware

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/j-ellette/apex-global-defense/services/oob-svc/internal/models"
)

// RequirePermission returns a middleware that allows the request only if the
// authenticated user holds the specified permission.
func RequirePermission(perm models.Permission) gin.HandlerFunc {
	return func(c *gin.Context) {
		claims := GetClaims(c)
		for _, p := range claims.Permissions {
			if p == perm {
				c.Next()
				return
			}
		}
		c.AbortWithStatusJSON(http.StatusForbidden, gin.H{
			"error":               "insufficient_permission",
			"required_permission": perm,
		})
	}
}
