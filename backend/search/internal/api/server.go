package api

import (
	"context"
	"encoding/json"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/rs/zerolog"

	"chat-agent/backend/search/internal/config"
	"chat-agent/backend/search/internal/search"
)

type Server struct {
	router *chi.Mux
}

func NewServer(cfg *config.Config, client *search.Client, logger zerolog.Logger) *Server {
	r := chi.NewRouter()
	r.Use(middleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	r.Get("/search/people", func(w http.ResponseWriter, r *http.Request) {
		query := r.URL.Query().Get("q")
		results, err := client.SearchPeople(r.Context(), query)
		if err != nil {
			logger.Error().Err(err).Msg("people search failed")
			http.Error(w, "search error", http.StatusBadGateway)
			return
		}
		json.NewEncoder(w).Encode(results)
	})

	r.Get("/search/smart", func(w http.ResponseWriter, r *http.Request) {
		query := r.URL.Query().Get("q")
		ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
		defer cancel()
		results, err := search.SmartSearch(ctx, query, cfg.SmartSearchSize, logger)
		if err != nil {
			logger.Error().Err(err).Msg("property search failed")
			http.Error(w, "search error", http.StatusBadGateway)
			return
		}
		// Defensive check: ensure results is never nil
		if results == nil {
			logger.Warn().Msg("SmartSearch returned nil, converting to empty slice")
			results = []search.DataItem{}
		}
		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(results); err != nil {
			logger.Error().Err(err).Msg("failed to encode response")
			http.Error(w, "encoding error", http.StatusInternalServerError)
			return
		}
	})

	return &Server{router: r}
}

func (s *Server) Router() *chi.Mux {
	return s.router
}
