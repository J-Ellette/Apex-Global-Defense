package middleware

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/j-ellette/apex-global-defense/services/oob-svc/internal/models"
)

// ClassificationGate returns a middleware that aborts the request if the
// authenticated user's classification ceiling is below the required level.
func ClassificationGate(required models.ClassificationLevel) gin.HandlerFunc {
	return func(c *gin.Context) {
		claims := GetClaims(c)
		if claims.Classification < required {
			c.AbortWithStatusJSON(http.StatusForbidden, gin.H{
				"error":    "classification_insufficient",
				"required": required.String(),
				"provided": claims.Classification.String(),
			})
			return
		}
		c.Next()
	}
}
