package handler

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/rs/zerolog"

	"chat-agent/backend/adapter/internal/ai"
	"chat-agent/backend/adapter/internal/config"
	"chat-agent/backend/adapter/internal/db"
	"chat-agent/backend/adapter/internal/models"
)

type ChatHandler struct {
	cfg    *config.Config
	repo   *db.Repository
	agent  *ai.Agent
	logger zerolog.Logger
}

func NewChatHandler(
	cfg *config.Config,
	repo *db.Repository,
	agent *ai.Agent,
	logger zerolog.Logger,
) *ChatHandler {
	return &ChatHandler{
		cfg:    cfg,
		repo:   repo,
		agent:  agent,
		logger: logger,
	}
}

type chatRequest struct {
	AgentID string `json:"agentId"`
	Message string `json:"message"`
}

type chatResponse struct {
	Message        responseMessage `json:"message"`
	ContextSummary string          `json:"contextSummary,omitempty"`
}

type responseMessage struct {
	ID        string `json:"id"`
	Role      string `json:"role"`
	Content   string `json:"content"`
	CreatedAt string `json:"createdAt"`
}

func (h *ChatHandler) HandleChat(w http.ResponseWriter, r *http.Request) {
	var req chatRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid payload", http.StatusBadRequest)
		return
	}

	ctx := r.Context()

	aiReq := ai.ChatRequest{
		Messages: []ai.Message{
			{Role: "user", Content: req.Message},
		},
	}

	profile, err := h.repo.GetAgentProfile(ctx, req.AgentID)
	if err != nil {
		h.logger.Error().Err(err).Str("agent_id", req.AgentID).Msg("failed to load profile")
		http.Error(w, "profile not found", http.StatusNotFound)
		return
	}

	reply, err := h.agent.Chat(ctx, aiReq, profile)
	if err != nil {
		h.logger.Error().Err(err).Msg("ai chat failed")
		http.Error(w, "failed to contact model", http.StatusBadGateway)
		return
	}

	now := time.Now().UTC()
	resp := chatResponse{
		Message: responseMessage{
			ID:        now.Format("20060102150405"),
			Role:      "assistant",
			Content:   reply.Message.Content,
			CreatedAt: now.Format(time.RFC3339),
		},
	}

	conversation := models.Conversation{
		AgentID:  req.AgentID,
		Query:    req.Message,
		Response: reply.Message.Content,
	}
	if err := h.repo.SaveConversation(ctx, &conversation); err != nil {
		h.logger.Warn().Err(err).Msg("failed to persist conversation")
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func composePrompt(system string, profile *models.AgentProfile) string {
	profileJSON, _ := json.Marshal(profile)
	return system + "\n\nAgent profile:\n" + string(profileJSON)
}
