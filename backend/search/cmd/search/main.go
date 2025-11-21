package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"github.com/rs/zerolog"

	"chat-agent/backend/search/internal/api"
	"chat-agent/backend/search/internal/config"
	"chat-agent/backend/search/internal/search"
	"chat-agent/backend/search/internal/version"
)

var MockDB []search.ElasticDataRecord

// LoadMockDB loads elastic-data.json into MockDB
func LoadMockDB() ([]search.ElasticDataRecord, error) {
	// Get the directory where the executable is located
	execPath, err := os.Executable()
	if err != nil {
		// Fallback to current working directory if we can't get executable path
		cwd, _ := os.Getwd()
		execPath = cwd
	}
	execDir := filepath.Dir(execPath)

	// Try multiple possible paths
	paths := []string{
		// Same directory as executable (for compiled binary)
		filepath.Join(execDir, "elastic-data.json"),
		// Relative to executable directory (cmd/search/)
		filepath.Join(execDir, "cmd", "search", "elastic-data.json"),
		// Current working directory
		"elastic-data.json",
		filepath.Join(".", "elastic-data.json"),
		// Relative to working directory
		filepath.Join("cmd", "search", "elastic-data.json"),
		filepath.Join("backend", "search", "cmd", "search", "elastic-data.json"),
	}

	// Add paths relative to current working directory
	if cwd, err := os.Getwd(); err == nil {
		paths = append(paths,
			filepath.Join(cwd, "elastic-data.json"),
			filepath.Join(cwd, "cmd", "search", "elastic-data.json"),
			filepath.Join(cwd, "backend", "search", "cmd", "search", "elastic-data.json"),
		)
	}

	var data []search.ElasticDataRecord
	var lastErr error

	for _, path := range paths {
		file, err := os.Open(path)
		if err != nil {
			lastErr = err
			continue
		}

		decoder := json.NewDecoder(file)
		if err := decoder.Decode(&data); err == nil {
			file.Close()
			return data, nil
		}
		file.Close()
		lastErr = err
	}

	return data, fmt.Errorf("failed to load elastic-data.json from any of the attempted paths: %w", lastErr)
}

func main() {
	logger := zerolog.New(os.Stdout).With().Timestamp().Str("version", version.BuildVersion).Logger()

	// // Load mock data
	// var err error
	// MockDB, err = LoadMockDB()
	// if err != nil {
	// 	logger.Warn().Err(err).Msg("failed to load elastic-data.json, continuing without mock data")
	// } else {
	// 	logger.Info().Int("records", len(MockDB)).Msg("loaded mock data")
	// 	// Set the mock data in the search package
	// 	search.SetMockDB(MockDB)
	// }

	cfg := config.Load()

	esClient, err := search.NewClient(cfg, logger.With().Str("component", "search").Logger())

	if err != nil {
		logger.Fatal().Err(err).Msg("failed to init elasticsearch")
	}

	server := api.NewServer(cfg, esClient, logger)

	httpServer := &http.Server{
		Addr:         cfg.ListenAddr,
		Handler:      server.Router(),
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 30 * time.Second,
	}

	go func() {
		logger.Info().Str("addr", cfg.ListenAddr).Msg("search service listening")
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatal().Err(err).Msg("server error")
		}
	}()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	<-stop

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := httpServer.Shutdown(ctx); err != nil {
		logger.Error().Err(err).Msg("graceful shutdown failed")
	}
}
