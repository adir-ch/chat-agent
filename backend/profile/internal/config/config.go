package config

import "os"

type Config struct {
	ListenAddr   string
	DatabasePath string
}

func Load() (*Config, error) {
	return &Config{
		ListenAddr:   envOr("PROFILE_LISTEN_ADDR", ":8080"),
		DatabasePath: envOr("PROFILE_DB_PATH", "./profile.db"),
	}, nil
}

func envOr(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}
