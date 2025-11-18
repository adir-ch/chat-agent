package search

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
)

// DataItem holds the exact fields we want from the result
type DataItem struct {
	EmailAddress  string `json:"emailaddress"`
	FullAddress   string `json:"full_address"`
	FullName      string `json:"full_name"`
	PhoneLandline string `json:"phone1_landline"`
	PhoneMobile   string `json:"phone2_mobile"`
}

// SmartSearchResponse matches only the fields we need
type SmartSearchResponse struct {
	Data []DataItem `json:"data"`
}

// SmartSearch performs the API call and extracts the required fields
func SmartSearch(ctx context.Context, query string) ([]DataItem, error) {

	// Read config from env
	apiURL := os.Getenv("ID4ME_API_URL")
	sessionID := os.Getenv("SESSION_ID")
	bearer := os.Getenv("BEARER_TOKEN")

	if apiURL == "" {
		return nil, fmt.Errorf("missing ID4ME_API_URL environment variable")
	}
	if sessionID == "" {
		return nil, fmt.Errorf("missing SESSION_ID environment variable")
	}
	if bearer == "" {
		return nil, fmt.Errorf("missing BEARER_TOKEN environment variable")
	}

	// Build JSON payload
	payload := map[string]interface{}{
		"query": query,
		"page":  0,
		"size":  50,
	}
	body, _ := json.Marshal(payload)

	// Create request WITH CONTEXT
	req, err := http.NewRequestWithContext(ctx, "POST", apiURL, bytes.NewBuffer(body))
	if err != nil {
		return nil, err
	}

	// Set required headers
	req.Header.Set("Accept", "application/json, text/plain, */*")
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+bearer)
	req.Header.Set("SessionId", sessionID)

	// Optional headers for compatibility
	req.Header.Set("Origin", "https://id4me.me")
	req.Header.Set("Referer", "https://id4me.me/")

	// Create client (or inject this if needed)
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

	respBytes, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var result SmartSearchResponse
	if err := json.Unmarshal(respBytes, &result); err != nil {
		fmt.Println("Raw response:", string(respBytes))
		return nil, fmt.Errorf("failed to parse JSON: %v", err)
	}

	return result.Data, nil
}
