package middleware

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/j-ellette/apex-global-defense/services/auth-svc/internal/models"
)

// RequireRole returns a middleware that allows the request only if the
// authenticated user has at least one of the specified roles.
func RequireRole(roles ...models.Role) gin.HandlerFunc {
	allowed := make(map[models.Role]struct{}, len(roles))
	for _, r := range roles {
		allowed[r] = struct{}{}
	}

	return func(c *gin.Context) {
		claims := GetClaims(c)
		for _, r := range claims.Roles {
			if _, ok := allowed[r]; ok {
				c.Next()
				return
			}
		}
		c.AbortWithStatusJSON(http.StatusForbidden, gin.H{
			"error":          "insufficient_role",
			"required_roles": roles,
		})
	}
}

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
