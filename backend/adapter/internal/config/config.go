package config

import "os"

type Config struct {
	ListenAddr   string
	DatabasePath string
	OllamaURL    string
	SearchURL    string
	SystemPrompt string
}

func Load() (*Config, error) {
	return &Config{
		ListenAddr:   envOr("ADAPTER_LISTEN_ADDR", ":8080"),
		DatabasePath: envOr("ADAPTER_DB_PATH", "adapter.db"),
		OllamaURL:    envOr("OLLAMA_URL", "http://localhost:11434"),
		SearchURL:    envOr("SEARCH_URL", "http://localhost:8090"),
		SystemPrompt: envOr("SYSTEM_PROMPT", defaultPrompt),
	}, nil
}

func envOr(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

const defaultPrompt = `You are Agent Assist, a helpful assistant for real estate agents.
Always personalise your answer using the agent profile and property data provided.
If function calls fail or return empty results, continue with the best answer possible.`

