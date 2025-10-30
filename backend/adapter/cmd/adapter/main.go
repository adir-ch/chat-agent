package main

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/rs/zerolog"

	"chat-agent/backend/adapter/internal/api"
	"chat-agent/backend/adapter/internal/config"
	"chat-agent/backend/adapter/internal/db"
)

func main() {
	logger := zerolog.New(os.Stdout).With().Timestamp().Logger()

	cfg, err := config.Load()
	if err != nil {
		logger.Fatal().Err(err).Msg("failed to load config")
	}

	sqlite, err := db.NewSQLite(cfg.DatabasePath)
	if err != nil {
		logger.Fatal().Err(err).Msg("failed to open sqlite database")
	}
	defer sqlite.Close()

	if err := db.ApplyMigrations(sqlite); err != nil {
		logger.Fatal().Err(err).Msg("failed to run migrations")
	}

	server := api.NewServer(cfg, sqlite, logger)

	httpServer := &http.Server{
		Addr:         cfg.ListenAddr,
		Handler:      server.Router(),
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 60 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	go func() {
		logger.Info().Str("addr", cfg.ListenAddr).Msg("adapter listening")
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

