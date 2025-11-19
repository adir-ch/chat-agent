package handler

import (
	"encoding/json"
	"net/http"

	"github.com/rs/zerolog"

	"chat-agent/backend/profile/internal/db"
	"chat-agent/backend/profile/internal/models"
)

type ConversationHandler struct {
	repo   *db.Repository
	logger zerolog.Logger
}

func NewConversationHandler(repo *db.Repository, logger zerolog.Logger) *ConversationHandler {
	return &ConversationHandler{
		repo:   repo,
		logger: logger,
	}
}

type saveConversationRequest struct {
	AgentID  string `json:"agentId"`
	Query    string `json:"query"`
	Response string `json:"response"`
}

func (h *ConversationHandler) HandleSaveConversation(w http.ResponseWriter, r *http.Request) {
	var req saveConversationRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid payload", http.StatusBadRequest)
		return
	}

	if req.AgentID == "" || req.Query == "" || req.Response == "" {
		http.Error(w, "agentId, query, and response are required", http.StatusBadRequest)
		return
	}

	ctx := r.Context()

	conversation := models.Conversation{
		AgentID:  req.AgentID,
		Query:    req.Query,
		Response: req.Response,
	}

	if err := h.repo.SaveConversation(ctx, &conversation); err != nil {
		h.logger.Error().Err(err).Msg("failed to save conversation")
		http.Error(w, "failed to save conversation", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}

