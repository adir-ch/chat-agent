package handler

import (
	"context"
	"encoding/json"
	"net/http"
	"time"

	"github.com/rs/zerolog"

	"chat-agent/backend/adapter/internal/config"
	"chat-agent/backend/adapter/internal/db"
	"chat-agent/backend/adapter/internal/models"
	"chat-agent/backend/adapter/internal/ollama"
	"chat-agent/backend/adapter/internal/search"
)

type ChatHandler struct {
	cfg          *config.Config
	repo         *db.Repository
	ollamaClient *ollama.Client
	searchClient *search.Client
	logger       zerolog.Logger
}

func NewChatHandler(
	cfg *config.Config,
	repo *db.Repository,
	ollamaClient *ollama.Client,
	searchClient *search.Client,
	logger zerolog.Logger,
) *ChatHandler {
	return &ChatHandler{
		cfg:          cfg,
		repo:         repo,
		ollamaClient: ollamaClient,
		searchClient: searchClient,
		logger:       logger,
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
	profile, err := h.repo.GetAgentProfile(ctx, req.AgentID)
	if err != nil {
		h.logger.Error().Err(err).Str("agent_id", req.AgentID).Msg("failed to load profile")
		http.Error(w, "profile not found", http.StatusNotFound)
		return
	}

	toolDefs := buildFunctionTools()
	prompt := composePrompt(h.cfg.SystemPrompt, profile)

	ollamaReq := ollama.ChatRequest{
		Messages: []ollama.Message{
			{Role: "system", Content: prompt},
			{Role: "user", Content: req.Message},
		},
		Tools: toolDefs,
	}

	reply, err := h.ollamaClient.Chat(ctx, ollamaReq)
	if err != nil {
		h.logger.Error().Err(err).Msg("ollama chat failed")
		http.Error(w, "failed to contact model", http.StatusBadGateway)
		return
	}

	finalContent, err := h.handleFunctionCalls(ctx, reply)
	if err != nil {
		h.logger.Error().Err(err).Msg("function call failed")
		http.Error(w, "function execution failed", http.StatusBadGateway)
		return
	}

	now := time.Now().UTC()
	resp := chatResponse{
		Message: responseMessage{
			ID:        now.Format("20060102150405"),
			Role:      "assistant",
			Content:   finalContent,
			CreatedAt: now.Format(time.RFC3339),
		},
	}

	conversation := models.Conversation{
		AgentID:  req.AgentID,
		Query:    req.Message,
		Response: finalContent,
	}
	if err := h.repo.SaveConversation(ctx, &conversation); err != nil {
		h.logger.Warn().Err(err).Msg("failed to persist conversation")
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}

func (h *ChatHandler) handleFunctionCalls(ctx context.Context, reply *ollama.ChatResponse) (string, error) {
	if len(reply.Message.ToolCalls) == 0 {
		return reply.Message.Content, nil
	}

	finalContent := reply.Message.Content

	for _, call := range reply.Message.ToolCalls {
		switch call.Function.Name {
		case "search_property":
			var args struct {
				Query string `json:"query"`
			}
			if err := json.Unmarshal(call.Function.Arguments, &args); err != nil {
				return "", err
			}
			results, err := h.searchClient.FetchProperty(ctx, args.Query)
			if err != nil {
				return "", err
			}
			finalContent = composeFunctionResponse(finalContent, "Property results", results)
		case "search_people":
			var args struct {
				Query string `json:"query"`
			}
			if err := json.Unmarshal(call.Function.Arguments, &args); err != nil {
				return "", err
			}
			results, err := h.searchClient.FetchPeople(ctx, args.Query)
			if err != nil {
				return "", err
			}
			finalContent = composeFunctionResponse(finalContent, "People results", results)
		}
	}
	return finalContent, nil
}

func composePrompt(system string, profile *models.AgentProfile) string {
	profileJSON, _ := json.Marshal(profile)
	return system + "\n\nAgent profile:\n" + string(profileJSON)
}

func composeFunctionResponse(original string, title string, payload json.RawMessage) string {
	return original + "\n\n" + title + ":\n" + string(payload)
}

func buildFunctionTools() []ollama.FunctionTool {
	propertySchema := json.RawMessage(`{
	  "type": "object",
	  "properties": {
	    "query": { "type": "string", "description": "Search keywords related to property listings" }
	  },
	  "required": ["query"]
	}`)

	peopleSchema := json.RawMessage(`{
	  "type": "object",
	  "properties": {
	    "query": { "type": "string", "description": "Search keywords for people or contacts" }
	  },
	  "required": ["query"]
	}`)

	return []ollama.FunctionTool{
		{
			Name:        "search_property",
			Description: "Find property listings or history relevant to the conversation",
			Parameters:  propertySchema,
		},
		{
			Name:        "search_people",
			Description: "Look up people data related to the query",
			Parameters:  peopleSchema,
		},
	}
}

