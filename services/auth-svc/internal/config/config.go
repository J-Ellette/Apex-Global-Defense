package config

import (
	"fmt"
	"strings"

	"github.com/spf13/viper"
)

// Config holds all application configuration.
type Config struct {
	Port        string `mapstructure:"PORT"`
	Env         string `mapstructure:"ENV"`
	DatabaseURL string `mapstructure:"DATABASE_URL"`
	RedisURL    string `mapstructure:"REDIS_URL"`
	JWTSecret   string `mapstructure:"JWT_SECRET"`
	JWTIssuer   string `mapstructure:"JWT_ISSUER"`
	// AccessToken TTL in minutes (default 15)
	AccessTokenTTL int `mapstructure:"ACCESS_TOKEN_TTL"`
	// RefreshToken TTL in hours (default 8)
	RefreshTokenTTL int    `mapstructure:"REFRESH_TOKEN_TTL"`
	KeycloakURL     string `mapstructure:"KEYCLOAK_URL"`
	KeycloakRealm   string `mapstructure:"KEYCLOAK_REALM"`
	KeycloakClient  string `mapstructure:"KEYCLOAK_CLIENT"`
}

// Load reads configuration from environment variables.
func Load() (*Config, error) {
	v := viper.New()

	v.SetDefault("PORT", "8080")
	v.SetDefault("ENV", "development")
	v.SetDefault("JWT_ISSUER", "agd-auth-svc")
	v.SetDefault("ACCESS_TOKEN_TTL", 15)
	v.SetDefault("REFRESH_TOKEN_TTL", 8)
	v.SetDefault("KEYCLOAK_REALM", "agd")
	v.SetDefault("KEYCLOAK_CLIENT", "agd-backend")
	v.SetDefault("DATABASE_URL", "")
	v.SetDefault("REDIS_URL", "")
	v.SetDefault("JWT_SECRET", "")
	v.SetDefault("KEYCLOAK_URL", "")

	v.AutomaticEnv()

	for _, key := range []string{"DATABASE_URL", "REDIS_URL", "JWT_SECRET", "KEYCLOAK_URL", "KEYCLOAK_REALM", "KEYCLOAK_CLIENT"} {
		if err := v.BindEnv(key); err != nil {
			return nil, fmt.Errorf("bind env %s: %w", key, err)
		}
	}

	cfg := &Config{}
	if err := v.Unmarshal(cfg); err != nil {
		return nil, err
	}

	missing := make([]string, 0, 4)
	if strings.TrimSpace(cfg.DatabaseURL) == "" {
		missing = append(missing, "DATABASE_URL")
	}
	if strings.TrimSpace(cfg.RedisURL) == "" {
		missing = append(missing, "REDIS_URL")
	}
	if strings.TrimSpace(cfg.JWTSecret) == "" {
		missing = append(missing, "JWT_SECRET")
	}
	if strings.TrimSpace(cfg.KeycloakURL) == "" {
		missing = append(missing, "KEYCLOAK_URL")
	}
	if len(missing) > 0 {
		return nil, fmt.Errorf("missing required environment variables: %s", strings.Join(missing, ", "))
	}

	return cfg, nil
}
