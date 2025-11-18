#!/bin/bash

# Search Service Test Script
# Tests the search service endpoints: /search/people and /search/smart

SEARCH_URL="${SEARCH_URL:-http://localhost:8090}"
QUERY="${1:-test}"

# SmartSearch environment variables (must be set in the search service environment)
# These can be set here for reference, but must be configured in the service:
export ID4ME_API_URL="https://id4me-search-prod-api.azurewebsites.net/api/Search/smart"
export SESSION_ID="2c73c8ce-1cd2-2c40-7b4c-5b20fae4193f"
export BEARER_TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IlF6VXhPVEkxUkRjd09ETXpNRUpFUlRjMU5EY3dPVUpFTmtNM05rSXdRVE5CTXpBMlFVUkdNUSJ9.eyJpc3MiOiJodHRwczovL2lkNG1lLmF1LmF1dGgwLmNvbS8iLCJzdWIiOiJhdXRoMHw2ODVhMjA1ODg1OThiZjg0MTZlZDUzOWYiLCJhdWQiOlsiIElkNG1lLXNlYXJjaC12MiIsImh0dHBzOi8vaWQ0bWUuYXUuYXV0aDAuY29tL3VzZXJpbmZvIl0sImlhdCI6MTc2MzQzMTQ4OSwiZXhwIjoxNzYzODYzNDg5LCJzY29wZSI6Im9wZW5pZCBwcm9maWxlIGVtYWlsIG9mZmxpbmVfYWNjZXNzIiwiYXpwIjoiYlgxU3dvR1B0Q08wV2RybnBSNHcweFhuREQ5N3MzSEUifQ.kBYNIqBxF1WOXvdC9ZLe7wcKXgq_3K3vV24JC1QS7O4d7muieGnQc1-YUL9RSL1VIyaE9SPQne6THCao3nMMFdK-9pPe9P33kK1wxUiW9NjjamKcdo8Zlu4U68PTzWZES0f5H3dX7ZJYqB1SPcUOdESQn-8pdRlri8sweyKF2d3HKTrSVcaRRnS61llDP5NvzubpnLeWslCXGEdJL2vZNnCGPqk-sNTvst5cSxO1y-YXf_jfPNBCWqcBuPWq9FkvP8_a7YYEbtZGqWTmI_RZHIfR6SbMCrLOYOKBc6PtKR0B9WyYYXGMIx5nbgDER6z20zcrTH4GkMoGLJ-DepCeMA"

echo "=========================================="
echo "Search Service Test"
echo "=========================================="
echo "Search URL: $SEARCH_URL"
echo "Query: $QUERY"
if [ -n "$ID4ME_API_URL" ] || [ -n "$SESSION_ID" ] || [ -n "$BEARER_TOKEN" ]; then
    echo ""
    echo "SmartSearch Environment Variables:"
    [ -n "$ID4ME_API_URL" ] && echo "  ID4ME_API_URL: ${ID4ME_API_URL:0:20}..." || echo "  ID4ME_API_URL: (not set)"
    [ -n "$SESSION_ID" ] && echo "  SESSION_ID: ${SESSION_ID:0:20}..." || echo "  SESSION_ID: (not set)"
    [ -n "$BEARER_TOKEN" ] && echo "  BEARER_TOKEN: ${BEARER_TOKEN:0:20}..." || echo "  BEARER_TOKEN: (not set)"
    echo "  Note: These must be set in the search service environment"
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
echo "Note: SmartSearch requires ID4ME_API_URL, SESSION_ID, and BEARER_TOKEN"
echo "      to be set in the search service environment"
echo "Request: GET $SEARCH_URL/search/smart?q=$QUERY"
echo ""
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" --get --data-urlencode "q=$QUERY" "$SEARCH_URL/search/smart")
HTTP_STATUS=$(echo "$RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

echo "HTTP Status: $HTTP_STATUS"
echo "Response Body:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

echo "=========================================="
echo "Test Complete"
echo "=========================================="

