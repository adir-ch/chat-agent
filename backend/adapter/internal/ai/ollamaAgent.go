package ai

import (
	"context"
	"fmt"
	"io/ioutil"
	"net/http"
	"net/url"
	"strings"

	"github.com/tmc/langchaingo/chains"
	"github.com/tmc/langchaingo/llms/ollama"
	"github.com/tmc/langchaingo/memory"
	"github.com/tmc/langchaingo/prompts"
)

// AgentProfile holds agent-specific details
type AgentProfile struct {
	Name           string
	Location       string
	RecentListings []string
}

// ConversationManager manages chat memory and interactions
type ConversationManager struct {
	llm     *ollama.LLM
	chain   *chains.LLMChain
	mem     *memory.Simple
	profile AgentProfile
}

// NewConversationManager creates an instance of ConversationManager
func NewConversationManager(profile AgentProfile) (*ConversationManager, error) {
	llm, err := ollama.New(ollama.WithModel("llama3")) // or any local model
	if err != nil {
		return nil, fmt.Errorf("failed to init ollama: %w", err)
	}

	template := `
You are a helpful assistant supporting real estate agent {{.AgentName}}.
They work in {{.Location}} and have recently listed: {{.Listings}}.

Maintain context across the chat using your memory.

If you need live homeowner or prospect data, respond ONLY with:
FETCH: <search terms to send to the data service>
Otherwise, answer normally.

{{.ConversationHistory}}
Question: {{.Question}}
`

	prompt := prompts.NewPromptTemplate(template,
		[]string{"AgentName", "Location", "Listings", "ConversationHistory", "Question"})

	mem := memory.NewSimple()

	chain := chains.NewLLMChain(llm, prompt)
	return &ConversationManager{
		llm:     llm,
		chain:   chain,
		mem:     mem,
		profile: profile,
	}, nil
}

// Ask allows multi-turn conversation with memory and data fetching
func (cm *ConversationManager) Ask(ctx context.Context, question string) (string, error) {
	history := cm.mem.String()

	input := map[string]any{
		"AgentName":           cm.profile.Name,
		"Location":            cm.profile.Location,
		"Listings":            strings.Join(cm.profile.RecentListings, ", "),
		"ConversationHistory": history,
		"Question":            question,
	}

	// Call the model
	initialAnswer, err := chains.Run(ctx, cm.chain, input)
	if err != nil {
		return "", fmt.Errorf("model failed: %w", err)
	}

	initialAnswer = strings.TrimSpace(initialAnswer)

	// Check if model requested data fetch
	if strings.HasPrefix(strings.ToUpper(initialAnswer), "FETCH:") {
		query := strings.TrimSpace(initialAnswer[6:])
		data, err := fetchPeople(query)
		if err != nil {
			return "", fmt.Errorf("failed to fetch data: %w", err)
		}

		followUp := fmt.Sprintf(
			"Here are the search results for '%s': %s. Please summarise the key opportunities for the agent.",
			query, data,
		)
		finalAnswer, err := cm.llm.Call(ctx, followUp)
		if err != nil {
			return "", fmt.Errorf("model follow-up failed: %w", err)
		}

		// Store in memory
		cm.mem.Add(question, finalAnswer)
		return strings.TrimSpace(finalAnswer), nil
	}

	// Otherwise, store normal response
	cm.mem.Add(question, initialAnswer)
	return initialAnswer, nil
}

// fetchPeople queries your local data API for homeowner data
func fetchPeople(query string) (string, error) {
	endpoint := "http://localhost:8090/search/people?q=" + url.QueryEscape(query)
	resp, err := http.Get(endpoint)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("endpoint returned %d", resp.StatusCode)
	}

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	return string(body), nil
}
