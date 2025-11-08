package ai

import (
	"chat-agent/backend/adapter/internal/models"
	"context"

	"github.com/tmc/langchaingo/prompts"
)

// Agent wraps an AI model for chat interactions.
// Implement this struct to provide your model wrapper.
type Agent struct {
	SystemPrompt string
}

// New creates a new AI agent.
// TODO: Implement this function with your initialization logic.
func New(systemPrompt string) *Agent {
	return &Agent{
		SystemPrompt: systemPrompt,
	}
}

// Message represents a chat message.
type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// ChatRequest represents a chat request to the AI model.
type ChatRequest struct {
	Messages []Message `json:"messages"`
}

// ChatResponse represents the response from the AI model.
type ChatResponse struct {
	Message Message `json:"message"`
}

// Chat sends a chat request to the AI model and returns the response.
// TODO: Implement this method with your model wrapper logic.
func (a *Agent) Chat(ctx context.Context, req ChatRequest, profile *models.AgentProfile) (*ChatResponse, error) {
	prompt := prompts.NewPromptTemplate(a.SystemPrompt,
		[]string{"AgentName", "Location", "Listings", "ConversationHistory", "Question"})
	return nil, nil
}
