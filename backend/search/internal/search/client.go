package search

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"

	es "github.com/elastic/go-elasticsearch/v8"

	"chat-agent/backend/search/internal/config"
)

type Client struct {
	elastic *es.Client
	cfg     *config.Config
}

func NewClient(cfg *config.Config) (*Client, error) {
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

func (c *Client) Search(ctx context.Context, index, query string) (*SearchResult, error) {
	body := map[string]any{
		"query": map[string]any{
			"multi_match": map[string]any{
				"query":  query,
				"fields": []string{"name^3", "description", "address", "suburb"},
			},
		},
		"size": 10,
	}
	payload, err := json.Marshal(body)
	if err != nil {
		return nil, err
	}

	res, err := c.elastic.Search(
		c.elastic.Search.WithContext(ctx),
		c.elastic.Search.WithIndex(index),
		c.elastic.Search.WithBody(bytes.NewReader(payload)),
	)
	if err != nil {
		return nil, err
	}
	defer res.Body.Close()

	if res.IsError() {
		return nil, fmt.Errorf("elasticsearch error: %s", res.String())
	}

	var parsed SearchResult
	if err := json.NewDecoder(res.Body).Decode(&parsed); err != nil {
		return nil, err
	}

	return &parsed, nil
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

