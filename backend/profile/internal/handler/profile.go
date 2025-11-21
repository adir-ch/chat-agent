package handler

import (
	"database/sql"
	"encoding/json"
	"errors"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/rs/zerolog"

	"chat-agent/backend/profile/internal/db"
)

type ProfileHandler struct {
	repo   *db.Repository
	logger zerolog.Logger
}

func NewProfileHandler(repo *db.Repository, logger zerolog.Logger) *ProfileHandler {
	return &ProfileHandler{
		repo:   repo,
		logger: logger,
	}
}

func (h *ProfileHandler) HandleGetProfile(w http.ResponseWriter, r *http.Request) {
	agentID := chi.URLParam(r, "agentId")
	if agentID == "" {
		http.Error(w, "agentId is required", http.StatusBadRequest)
		return
	}

	h.logger.Debug().Str("agent_id", agentID).Msg("fetching profile")

	ctx := r.Context()

	profile, err := h.repo.GetAgentProfile(ctx, agentID)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			h.logger.Warn().Str("agent_id", agentID).Msg("profile not found")
			http.Error(w, "profile not found", http.StatusNotFound)
			return
		}
		h.logger.Error().Err(err).Str("agent_id", agentID).Msg("failed to load profile from database")
		http.Error(w, "internal server error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(profile); err != nil {
		h.logger.Error().Err(err).Msg("failed to encode profile response")
		http.Error(w, "internal server error", http.StatusInternalServerError)
		return
	}
}

func (h *ProfileHandler) HandleGetAgents(w http.ResponseWriter, r *http.Request) {
	h.logger.Debug().Msg("fetching all agents")

	ctx := r.Context()

	agents, err := h.repo.GetAllAgents(ctx)
	if err != nil {
		h.logger.Error().Err(err).Msg("failed to load agents from database")
		http.Error(w, "internal server error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(agents); err != nil {
		h.logger.Error().Err(err).Msg("failed to encode agents response")
		http.Error(w, "internal server error", http.StatusInternalServerError)
		return
	}
}
