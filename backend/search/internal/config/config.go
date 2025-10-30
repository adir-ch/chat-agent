package config

import "os"

type Config struct {
	ListenAddr    string
	ESAddress     string
	IndexPeople   string
	IndexProperty string
}

func Load() *Config {
	return &Config{
		ListenAddr:    envOr("SEARCH_LISTEN_ADDR", ":8090"),
		ESAddress:     envOr("ELASTICSEARCH_URL", "http://localhost:9200"),
		IndexPeople:   envOr("ES_INDEX_PEOPLE", "people"),
		IndexProperty: envOr("ES_INDEX_PROPERTY", "properties"),
	}
}

func envOr(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

