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

var defaultPrompt = `
You are a helpful assistant supporting real estate agent {{.AgentName}}.
They work in {{.Location}} and have recently listed: {{.Listings}}.

Maintain context across the chat using your memory.

If you need live homeowner or prospect data, respond ONLY with:
FETCH: <search terms to send to the data service>
Otherwise, answer normally.

{{.ConversationHistory}}
Question: {{.Question}}
`
