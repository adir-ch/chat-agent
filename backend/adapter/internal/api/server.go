package api

import (
	"database/sql"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/rs/zerolog"

	"chat-agent/backend/adapter/internal/config"
	"chat-agent/backend/adapter/internal/db"
	"chat-agent/backend/adapter/internal/handler"
	"chat-agent/backend/adapter/internal/ollama"
	"chat-agent/backend/adapter/internal/search"
)

type Server struct {
	router *chi.Mux
}

func NewServer(cfg *config.Config, dbConn *sql.DB, logger zerolog.Logger) *Server {
	repo := db.NewRepository(dbConn)
	ollamaClient := ollama.New(cfg.OllamaURL, "llama3.1")
	searchClient := search.NewClient(cfg.SearchURL)

	chatHandler := handler.NewChatHandler(cfg, repo, ollamaClient, searchClient, logger)

	r := chi.NewRouter()
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	r.Post("/api/chat", chatHandler.HandleChat)

	return &Server{router: r}
}

func (s *Server) Router() *chi.Mux {
	return s.router
}

