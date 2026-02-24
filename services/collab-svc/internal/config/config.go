package config

import (
	"github.com/spf13/viper"
)

// Config holds all configuration for the collab service.
type Config struct {
	Port      string `mapstructure:"PORT"`
	Env       string `mapstructure:"ENV"`
	JWTSecret string `mapstructure:"JWT_SECRET"`
	RedisURL  string `mapstructure:"REDIS_URL"`
}

// Load reads configuration from environment variables and optional .env file.
func Load() (*Config, error) {
	v := viper.New()
	v.AutomaticEnv()

	v.SetDefault("PORT", "8080")
	v.SetDefault("ENV", "development")
	v.SetDefault("JWT_SECRET", "dev-secret-change-in-prod")
	v.SetDefault("REDIS_URL", "redis://localhost:6379")

	cfg := &Config{}
	if err := v.Unmarshal(cfg); err != nil {
		return nil, err
	}
	return cfg, nil
}
