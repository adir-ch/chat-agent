#!/bin/bash

# Search Service Test Script
# Tests the search service endpoints: /search/people and /search/smart

SEARCH_URL="${SEARCH_URL:-http://localhost:8090}"
QUERY="${1:-test}"

# SmartSearch environment variables (must be set in the search service environment)
# The API endpoint is hardcoded to https://admin.id4me.me/SearchAPI
# Only the API key needs to be configured:
# export ID4ME_API_KEY="your-api-key-here"

echo "=========================================="
echo "Search Service Test"
echo "=========================================="
echo "Search URL: $SEARCH_URL"
echo "Query: $QUERY"
if [ -n "$ID4ME_API_KEY" ]; then
    echo ""
    echo "SmartSearch Environment Variables:"
    echo "  ID4ME_API_KEY: ${ID4ME_API_KEY:0:20}..."
    echo "  Note: This must be set in the search service environment"
    echo "  API Endpoint: https://admin.id4me.me/SearchAPI (hardcoded)"
else
    echo ""
    echo "SmartSearch Environment Variables:"
    echo "  ID4ME_API_KEY: (not set)"
    echo "  Note: ID4ME_API_KEY must be set in the search service environment"
    echo "  API Endpoint: https://admin.id4me.me/SearchAPI (hardcoded)"
fi
echo ""

# Test people search
# echo "----------------------------------------"
# echo "Testing /search/people endpoint"
# echo "----------------------------------------"
# echo "Request: GET $SEARCH_URL/search/people?q=$QUERY"
# echo ""
# RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$SEARCH_URL/search/people?q=$QUERY")
# HTTP_STATUS=$(echo "$RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
# BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

# echo "HTTP Status: $HTTP_STATUS"
# echo "Response Body:"
# echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
# echo ""

# Test smart search
echo "----------------------------------------"
echo "Testing /search/smart endpoint"
echo "----------------------------------------"
echo "Note: SmartSearch requires ID4ME_API_KEY"
echo "      to be set in the search service environment"
echo "      API endpoint is hardcoded to https://admin.id4me.me/SearchAPI"
echo "Request: GET $SEARCH_URL/search/smart?q=$QUERY"
echo ""
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" --get --data-urlencode "q=$QUERY" "$SEARCH_URL/search/smart")
# Extract HTTP status from the last line
HTTP_STATUS=$(echo "$RESPONSE" | tail -n 1 | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
# Extract body by removing the last line (which contains HTTP_STATUS)
# Using sed '$d' which works on both BSD (macOS) and GNU sed
BODY=$(echo "$RESPONSE" | sed '$d')

echo "HTTP Status: $HTTP_STATUS"
echo "Response Body:"
if [ -z "$BODY" ]; then
    echo "(empty response)"
elif echo "$BODY" | jq . >/dev/null 2>&1; then
    echo "$BODY" | jq '.'
else
    echo "Raw response (not valid JSON):"
    echo "$BODY"
fi
echo ""

echo "=========================================="
echo "Test Complete"
echo "=========================================="

