package search

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"

	"github.com/rs/zerolog"
)

// DataItem holds the exact fields we want from the result
type DataItem struct {
	EmailAddress  string `json:"emailaddress"`
	FullAddress   string `json:"full_address"`
	FullName      string `json:"full_name"`
	PhoneLandline string `json:"phone1_landline"`
	PhoneMobile   string `json:"phone2_mobile"`
}

// RecordResponse represents the nested Record object structure
type RecordResponse struct {
	RecCount    int        `json:"recCount"`
	RecRelation string     `json:"recRelation"`
	Elapsed     int        `json:"elapsed"`
	ErrorCode   int        `json:"errorCode"`
	Record      []DataItem `json:"record"` // The actual array of records
	More        bool       `json:"more"`
	Keys        string     `json:"keys"`
}

// SmartSearchResponse matches the API response structure
type SmartSearchResponse struct {
	People      []DataItem      `json:"people"` // Legacy field (may not be present)
	Record      *RecordResponse `json:"Record"` // Nested Record object
	RecCount    int             `json:"RecCount"`
	RecRelation string          `json:"RecRelation"`
	Elapsed     int             `json:"Elapsed"`
	Error       *string         `json:"Error"`
	ErrorCode   int             `json:"ErrorCode"`
	More        bool            `json:"More"`
	Keys        *string         `json:"Keys"`
}

// SmartSearch performs the API call and extracts the required fields
func SmartSearch(ctx context.Context, query string, logger zerolog.Logger) ([]DataItem, error) {
	// Read API key from env
	apiKey := os.Getenv("ID4ME_API_KEY")
	if apiKey == "" {
		return nil, fmt.Errorf("missing ID4ME_API_KEY environment variable")
	}

	// Hardcoded API URL
	apiURL := "https://admin.id4me.me/SearchAPI"

	// Build JSON payload matching new API format
	payload := map[string]interface{}{
		"page":     0,
		"size":     30,
		"querytag": "json",
		"request": []map[string]interface{}{
			{
				"id":      0,
				"command": "query",
				"arg":     query,
			},
		},
		"index": "search-au",
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal payload: %v", err)
	}

	// Create request WITH CONTEXT
	req, err := http.NewRequestWithContext(ctx, "POST", apiURL, bytes.NewBuffer(body))
	if err != nil {
		return nil, err
	}

	// Set required headers
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", apiKey)

	// Create client
	client := &http.Client{}

	// --- IMPORTANT ---
	// This call uses the context because it is embedded in the request.
	// If ctx is cancelled or times out, this Do() call is aborted.
	// ------------------
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	// Check HTTP status code
	if resp.StatusCode != http.StatusOK {
		respBytes, _ := io.ReadAll(resp.Body)
		logger.Error().Int("status", resp.StatusCode).Str("body", string(respBytes)).Msg("API returned non-200 status")
		return nil, fmt.Errorf("API returned status %d: %s", resp.StatusCode, string(respBytes))
	}

	respBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var result SmartSearchResponse
	if err := json.Unmarshal(respBytes, &result); err != nil {
		logger.Error().Msgf("failed to parse JSON: %v", err)
		logger.Error().Msgf("response body was: %s", string(respBytes))
		return nil, fmt.Errorf("failed to parse JSON: %v", err)
	}

	// Use Record field if People is empty (API uses nested "Record.record" structure)
	var results []DataItem
	if len(result.People) > 0 {
		results = result.People
		logger.Info().Int("results_received", len(results)).Msg("received results from People field")
	} else if result.Record != nil && len(result.Record.Record) > 0 {
		results = result.Record.Record
		logger.Info().Int("results_received", len(results)).Msg("received results from Record field")
	} else {
		logger.Info().Int("results_received", 0).Msg("no results received from API")
	}

	// Check for API errors
	if result.Error != nil && *result.Error != "" {
		return nil, fmt.Errorf("API error: %s (ErrorCode: %d)", *result.Error, result.ErrorCode)
	}

	// Return results array (from either People or Record.record field)
	// Ensure we return an empty slice instead of nil to avoid encoding as null
	if results == nil {
		logger.Warn().Msg("no results found in API response")
		return []DataItem{}, nil
	}

	return results, nil
}
