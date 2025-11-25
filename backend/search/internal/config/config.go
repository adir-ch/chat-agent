package config

import (
	"os"
	"strconv"
)

type Config struct {
	ListenAddr      string
	ESAddress       string
	IndexPeople     string
	IndexProperty   string
	SmartSearchSize int
}

func Load() *Config {
	return &Config{
		ListenAddr:      envOr("SEARCH_LISTEN_ADDR", ":8090"),
		ESAddress:       envOr("ELASTICSEARCH_URL", "http://localhost:9200"),
		IndexPeople:     envOr("ES_INDEX_PEOPLE", "people"),
		IndexProperty:   envOr("ES_INDEX_PROPERTY", "properties"),
		SmartSearchSize: envIntOr("SMART_SEARCH_SIZE", 15),
	}
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
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
