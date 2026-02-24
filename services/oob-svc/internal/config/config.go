package config

import "github.com/spf13/viper"

// Config holds all application configuration for oob-svc.
type Config struct {
	Port        string `mapstructure:"PORT"`
	Env         string `mapstructure:"ENV"`
	DatabaseURL string `mapstructure:"DATABASE_URL"`
	JWTSecret   string `mapstructure:"JWT_SECRET"`
	JWTIssuer   string `mapstructure:"JWT_ISSUER"`
}

// Load reads configuration from environment variables.
func Load() (*Config, error) {
	v := viper.New()

	v.SetDefault("PORT", "8080")
	v.SetDefault("ENV", "development")
	v.SetDefault("JWT_ISSUER", "agd-auth-svc")

	v.AutomaticEnv()

	cfg := &Config{}
	if err := v.Unmarshal(cfg); err != nil {
		return nil, err
	}

	return cfg, nil
}
