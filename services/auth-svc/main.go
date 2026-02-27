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

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
	"github.com/redis/go-redis/v9"
	"go.uber.org/zap"

	"github.com/j-ellette/apex-global-defense/services/auth-svc/internal/config"
	"github.com/j-ellette/apex-global-defense/services/auth-svc/internal/handlers"
	"github.com/j-ellette/apex-global-defense/services/auth-svc/internal/middleware"
	"github.com/j-ellette/apex-global-defense/services/auth-svc/internal/store"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		fmt.Fprintf(os.Stderr, "failed to load config: %v\n", err)
		os.Exit(1)
	}

	// Logger
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

	// Database — retry up to 10 times with linear backoff to survive slow container DNS.
	var db *sqlx.DB
	for i := 1; i <= 10; i++ {
		db, err = sqlx.Connect("postgres", cfg.DatabaseURL)
		if err == nil {
			break
		}
		log.Warn("database not ready, retrying", zap.Int("attempt", i), zap.Error(err))
		time.Sleep(time.Duration(i) * time.Second)
	}
	if err != nil {
		log.Fatal("failed to connect to database", zap.Error(err))
	}
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)

	// Redis
	rdbOpts, err := redis.ParseURL(cfg.RedisURL)
	if err != nil {
		log.Fatal("failed to parse redis URL", zap.Error(err))
	}
	rdb := redis.NewClient(rdbOpts)
	if err := rdb.Ping(context.Background()).Err(); err != nil {
		log.Fatal("failed to connect to redis", zap.Error(err))
	}

	// Stores
	userStore := store.NewUserStore(db)
	sessionStore := store.NewSessionStore(&redisSessionAdapter{rdb})

	// Handlers
	authHandler := handlers.NewAuthHandler(
		userStore,
		sessionStore,
		cfg.JWTSecret,
		cfg.JWTIssuer,
		time.Duration(cfg.AccessTokenTTL)*time.Minute,
		time.Duration(cfg.RefreshTokenTTL)*time.Hour,
		log,
	)

	// Router
	if cfg.Env == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	r := gin.New()
	r.Use(cors.New(cors.Config{
		AllowOrigins: []string{
			"http://localhost:5173",
			"http://127.0.0.1:5173",
		},
		AllowMethods: []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowHeaders: []string{"Origin", "Content-Type", "Accept", "Authorization"},
		MaxAge:       12 * time.Hour,
	}))
	r.Use(gin.Recovery())
	r.Use(requestLogger(log))

	// Health check
	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "ok"})
	})

	// Auth routes (unauthenticated)
	authGroup := r.Group("/api/v1/auth")
	{
		authGroup.POST("/login", authHandler.Login)
		authGroup.POST("/refresh", authHandler.Refresh)
		authGroup.POST("/logout", authHandler.Logout)
	}

	// Protected auth routes
	protected := r.Group("/api/v1/auth")
	protected.Use(middleware.JWTAuth(cfg.JWTSecret))
	{
		protected.GET("/me", authHandler.Me)
	}

	// Server
	srv := &http.Server{
		Addr:         ":" + cfg.Port,
		Handler:      r,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		log.Info("auth-svc starting", zap.String("port", cfg.Port), zap.String("env", cfg.Env))
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			log.Fatal("server error", zap.Error(err))
		}
	}()

	<-quit
	log.Info("shutting down auth-svc...")

	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Error("server forced shutdown", zap.Error(err))
	}

	log.Info("auth-svc stopped")
}

// requestLogger is a simple Gin middleware that logs each request.
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

// redisSessionAdapter adapts *redis.Client to the interface expected by store.NewSessionStore.
type redisSessionAdapter struct {
	rdb *redis.Client
}

func (a *redisSessionAdapter) Set(ctx context.Context, key string, value interface{}, expiration time.Duration) error {
	return a.rdb.Set(ctx, key, value, expiration).Err()
}

func (a *redisSessionAdapter) Get(ctx context.Context, key string) (string, error) {
	return a.rdb.Get(ctx, key).Result()
}

func (a *redisSessionAdapter) Del(ctx context.Context, keys ...string) error {
	return a.rdb.Del(ctx, keys...).Err()
}
