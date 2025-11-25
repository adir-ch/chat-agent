package config

import (
	"os"
	"strconv"
)

type Config struct {
	ListenAddr       string
	DatabasePath     string
	ListingsLimit    int
}

func Load() (*Config, error) {
	return &Config{
		ListenAddr:    envOr("PROFILE_LISTEN_ADDR", ":8080"),
		DatabasePath:   envOr("PROFILE_DB_PATH", "./profile.db"),
		ListingsLimit: envIntOr("PROFILE_LISTINGS_LIMIT", 5),
	}, nil
}

func envOr(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func envIntOr(key string, fallback int) int {
	if v := os.Getenv(key); v != "" {
		if i, err := strconv.Atoi(v); err == nil {
			return i
		}
	}
	return fallback
}
