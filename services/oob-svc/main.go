package main

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
	"go.uber.org/zap"

	"github.com/j-ellette/apex-global-defense/services/oob-svc/internal/config"
	"github.com/j-ellette/apex-global-defense/services/oob-svc/internal/handlers"
	"github.com/j-ellette/apex-global-defense/services/oob-svc/internal/middleware"
	"github.com/j-ellette/apex-global-defense/services/oob-svc/internal/store"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to load config: %v\n", err)
		os.Exit(1)
	}

	var log *zap.Logger
	if cfg.Env == "production" {
		log, err = zap.NewProduction()
	} else {
		log, err = zap.NewDevelopment()
	}
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to init logger: %v\n", err)
		os.Exit(1)
	}
	defer log.Sync() //nolint:errcheck

	db, err := sqlx.Connect("postgres", cfg.DatabaseURL)
	if err != nil {
		log.Fatal("failed to connect to database", zap.Error(err))
	}
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)

	oobStore := store.NewOOBStore(db)
	oobHandler := handlers.NewOOBHandler(oobStore, log)
	scenarioHandler := handlers.NewScenarioHandler(oobStore, log)

	// Audit callback — writes to audit_log table asynchronously.
	auditFn := func(userID uuid.UUID, action, resourceType, ip, ua string) {
		oobStore.WriteAuditLogAsync(store.AuditEntry{
			UserID:       userID,
			Action:       action,
			ResourceType: resourceType,
			IPAddress:    ip,
			UserAgent:    ua,
		})
	}

	if cfg.Env == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	r := gin.New()
	r.Use(gin.Recovery())
	r.Use(requestLogger(log))

	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "ok"})
	})

	// All OOB routes require a valid JWT.
	oob := r.Group("/api/v1/oob")
	oob.Use(middleware.JWTAuth(cfg.JWTSecret))

	// Read-only routes require oob:read permission.
	oob.GET("/countries", oobHandler.ListCountries)
	oob.GET("/countries/:code", oobHandler.GetCountry)
	oob.GET("/countries/:code/forces", oobHandler.ListForces)
	oob.GET("/units/:id", oobHandler.GetUnit)
	oob.GET("/units/:id/history", oobHandler.UnitHistory)
	oob.POST("/compare", oobHandler.CompareCountries)
	oob.GET("/equipment/catalog", oobHandler.ListEquipmentCatalog)

	// Write routes require oob:write permission.
	write := oob.Group("")
	write.Use(middleware.RequirePermission("oob:write"))
	write.Use(middleware.AuditWrites(auditFn, log))
	write.POST("/units", oobHandler.CreateUnit)
	write.PUT("/units/:id", oobHandler.UpdateUnit)
	write.DELETE("/units/:id", oobHandler.DeleteUnit)

	// Scenario routes — read requires scenario:read, write requires scenario:write.
	scenarios := r.Group("/api/v1/scenarios")
	scenarios.Use(middleware.JWTAuth(cfg.JWTSecret))
	scenarios.Use(middleware.RequirePermission("scenario:read"))
	scenarios.GET("", scenarioHandler.ListScenarios)
	scenarios.GET("/:id", scenarioHandler.GetScenario)

	scenarioWrite := scenarios.Group("")
	scenarioWrite.Use(middleware.RequirePermission("scenario:write"))
	scenarioWrite.Use(middleware.AuditWrites(auditFn, log))
	scenarioWrite.POST("", scenarioHandler.CreateScenario)
	scenarioWrite.PUT("/:id", scenarioHandler.UpdateScenario)
	scenarioWrite.DELETE("/:id", scenarioHandler.DeleteScenario)
	scenarioWrite.POST("/:id/branch", scenarioHandler.BranchScenario)

	srv := &http.Server{
		Addr:         ":" + cfg.Port,
		Handler:      r,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		log.Info("oob-svc starting", zap.String("port", cfg.Port), zap.String("env", cfg.Env))
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			log.Fatal("server error", zap.Error(err))
		}
	}()

	<-quit
	log.Info("shutting down oob-svc...")

	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Error("server forced shutdown", zap.Error(err))
	}

	log.Info("oob-svc stopped")
}

func requestLogger(log *zap.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		c.Next()
		log.Info("request",
			zap.String("method", c.Request.Method),
			zap.String("path", c.Request.URL.Path),
			zap.Int("status", c.Writer.Status()),
			zap.Duration("latency", time.Since(start)),
			zap.String("ip", c.ClientIP()),
		)
	}
}
