package middleware

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"go.uber.org/zap"
)

// AuditFn is a callback invoked by the AuditWrites middleware after each
// successful mutating request. Implementations must be non-blocking.
type AuditFn func(userID uuid.UUID, action, resourceType, ip, userAgent string)

// AuditWrites returns a middleware that calls fn for every mutating request
// (POST, PUT, PATCH, DELETE) that completes with a 2xx status code.
// The call is made synchronously but fn itself should be non-blocking
// (e.g., spawn a goroutine internally for DB writes).
func AuditWrites(fn AuditFn, log *zap.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Next()

		method := c.Request.Method
		if method != http.MethodPost &&
			method != http.MethodPut &&
			method != http.MethodPatch &&
			method != http.MethodDelete {
			return
		}
		if c.Writer.Status() < 200 || c.Writer.Status() >= 300 {
			return
		}

		claims := GetClaims(c)
		userID, err := uuid.Parse(claims.UserID)
		if err != nil {
			log.Warn("audit: invalid user id", zap.String("uid", claims.UserID))
			return
		}

		action := method + " " + c.FullPath()
		ip := c.ClientIP()
		ua := c.GetHeader("User-Agent")
		resourceType := resourceTypeFromPath(c.FullPath())

		log.Info("audit",
			zap.String("user_id", claims.UserID),
			zap.String("action", action),
			zap.String("resource_type", resourceType),
			zap.String("ip", ip),
			zap.Int("status", c.Writer.Status()),
		)

		fn(userID, action, resourceType, ip, ua)
	}
}

// resourceTypeFromPath extracts a resource type string from a Gin route pattern.
func resourceTypeFromPath(path string) string {
	switch {
	case strings.Contains(path, "/units"):
		return "military_unit"
	case strings.Contains(path, "/scenarios") && strings.Contains(path, "/branch"):
		return "scenario_branch"
	case strings.Contains(path, "/scenarios"):
		return "scenario"
	case strings.Contains(path, "/equipment"):
		return "equipment"
	default:
		return "unknown"
	}
}

