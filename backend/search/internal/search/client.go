package search

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	es "github.com/elastic/go-elasticsearch/v8"
	"github.com/rs/zerolog"

	"chat-agent/backend/search/internal/config"
)

// ElasticDataRecord represents a single record from elastic-data.json
type ElasticDataRecord struct {
	ID   string     `json:"id"`
	Data PersonData `json:"data"`
}

// PersonData represents the data object within each record
type PersonData struct {
	Name         *PersonName    `json:"name,omitempty"`
	Address      *PersonAddress `json:"address,omitempty"`
	Mobile       string         `json:"mobile,omitempty"`
	Email        string         `json:"email,omitempty"`
	LastSeenDate string         `json:"last-seen-date,omitempty"`
}

// PersonName represents the name object
type PersonName struct {
	First string `json:"first,omitempty"`
	Last  string `json:"last,omitempty"`
}

// PersonAddress represents the address object
type PersonAddress struct {
	StreetNumber string `json:"street-number,omitempty"`
	StreetName   string `json:"street-name,omitempty"`
	Suburb       string `json:"suburb,omitempty"`
	State        string `json:"state,omitempty"`
	PostCode     string `json:"post-code,omitempty"`
}

type Client struct {
	elastic *es.Client
	cfg     *config.Config
	logger  zerolog.Logger
}

func NewClient(cfg *config.Config, logger zerolog.Logger) (*Client, error) {
	client, err := es.NewClient(es.Config{
		Addresses: []string{cfg.ESAddress},
	})
	if err != nil {
		return nil, err
	}
	return &Client{
		elastic: client,
		cfg:     cfg,
	}, nil
}

type SearchResult struct {
	Hits struct {
		Hits []struct {
			ID     string                 `json:"_id"`
			Source map[string]interface{} `json:"_source"`
		} `json:"hits"`
	} `json:"hits"`
}

// func (c *Client) Search(ctx context.Context, index, query string) (*SearchResult, error) {
// 	body := map[string]any{
// 		"query": map[string]any{
// 			"multi_match": map[string]any{
// 				"query":  query,
// 				"fields": []string{"name^3", "description", "address", "suburb"},
// 			},
// 		},
// 		"size": 10,
// 	}
// 	payload, err := json.Marshal(body)
// 	if err != nil {
// 		return nil, err
// 	}

// 	res, err := c.elastic.Search(
// 		c.elastic.Search.WithContext(ctx),
// 		c.elastic.Search.WithIndex(index),
//	}
// 	if res.IsError() {
// 		return nil, fmt.Errorf("elasticsearch error: %s", res.String())
// 	}

// 	var parsed SearchResult
// 	if err := json.NewDecoder(res.Body).Decode(&parsed); err != nil {
// 		return nil, err
// 	}

//		return &parsed, nil
//	}

// mockDB holds the loaded elastic-data.json records (set via SetMockDB)
var mockDB []ElasticDataRecord

// SetMockDB sets the mock database for testing/searching
func SetMockDB(data []ElasticDataRecord) {
	mockDB = data
}

// searchInValue recursively searches for a query string in any value (case-insensitive)
func searchInValue(value interface{}, query string) bool {
	queryLower := strings.ToLower(query)

	switch v := value.(type) {
	case map[string]interface{}:
		for _, val := range v {
			if searchInValue(val, query) {
				return true
			}
		}
	case []interface{}:
		for _, item := range v {
			if searchInValue(item, query) {
				return true
			}
		}
	case string:
		return strings.Contains(strings.ToLower(v), queryLower)
	case float64, int, int64, float32:
		return strings.Contains(strings.ToLower(fmt.Sprintf("%v", v)), queryLower)
	case bool:
		return strings.Contains(strings.ToLower(fmt.Sprintf("%v", v)), queryLower)
	}

	return false
}

// recordToMap converts an ElasticDataRecord to a map[string]interface{} for SearchResult
func recordToMap(record ElasticDataRecord) map[string]interface{} {
	// Convert to JSON and back to map to handle nested structures properly
	jsonBytes, _ := json.Marshal(record)
	var result map[string]interface{}
	json.Unmarshal(jsonBytes, &result)
	return result
}

// matchesQuery checks if any field in the record matches the query string
func matchesQuery(record ElasticDataRecord, query string) bool {
	// Convert record to map for recursive searching
	recordMap := recordToMap(record)
	return searchInValue(recordMap, query)
}

func (c *Client) Search(ctx context.Context, index, query string) (*SearchResult, error) {
	if query == "" {
		return &SearchResult{}, nil
	}

	// Search through mockDB records
	var matches []ElasticDataRecord
	for _, record := range mockDB {
		if matchesQuery(record, query) {
			matches = append(matches, record)
		}
	}

	// Convert matches to SearchResult format
	result := &SearchResult{}
	for _, record := range matches {
		hit := struct {
			ID     string                 `json:"_id"`
			Source map[string]interface{} `json:"_source"`
		}{
			ID:     record.ID,
			Source: recordToMap(record),
		}
		result.Hits.Hits = append(result.Hits.Hits, hit)
	}

	return result, nil
}

func formatResult(result *SearchResult) []map[string]interface{} {
	items := make([]map[string]interface{}, 0, len(result.Hits.Hits))
	for _, hit := range result.Hits.Hits {
		item := map[string]interface{}{
			"id": hit.ID,
		}
		for key, value := range hit.Source {
			item[key] = value
		}
		items = append(items, item)
	}
	return items
}

func (c *Client) SearchPeople(ctx context.Context, query string) ([]map[string]interface{}, error) {
	result, err := c.Search(ctx, c.cfg.IndexPeople, query)
	if err != nil {
		return nil, err
	}
	return formatResult(result), nil
}

func (c *Client) SearchProperty(ctx context.Context, query string) ([]map[string]interface{}, error) {
	result, err := c.Search(ctx, c.cfg.IndexProperty, query)
	if err != nil {
		return nil, err
	}
	return formatResult(result), nil
}
