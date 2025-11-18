package search

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
)

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

// SearchMockDB searches through the mock database
func SearchMockDB(ctx context.Context, index, query string) (*SearchResult, error) {
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
