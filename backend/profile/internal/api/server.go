package api

import (
	"database/sql"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
	"github.com/rs/zerolog"

	"chat-agent/backend/profile/internal/config"
	"chat-agent/backend/profile/internal/db"
	"chat-agent/backend/profile/internal/handler"
)

type Server struct {
	router *chi.Mux
}

func NewServer(cfg *config.Config, dbConn *sql.DB, logger zerolog.Logger) *Server {
	repo := db.NewRepository(dbConn)

	profileHandler := handler.NewProfileHandler(repo, logger)
	conversationHandler := handler.NewConversationHandler(repo, logger)

	r := chi.NewRouter()
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   []string{"http://localhost:5173", "http://localhost:3000"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-CSRF-Token"},
		ExposedHeaders:   []string{"Link"},
		AllowCredentials: true,
		MaxAge:           300,
	}))

	r.Get("/api/profile/{agentId}", profileHandler.HandleGetProfile)
	r.Get("/api/agents", profileHandler.HandleGetAgents)
	r.Post("/api/conversations", conversationHandler.HandleSaveConversation)

	return &Server{router: r}
}

func (s *Server) Router() *chi.Mux {
	return s.router
}
