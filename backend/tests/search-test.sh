#!/bin/bash

# Search Service Test Script
# Tests the search service endpoints: /search/people and /search/property

SEARCH_URL="${SEARCH_URL:-http://localhost:8090}"
QUERY="${1:-test}"

echo "=========================================="
echo "Search Service Test"
echo "=========================================="
echo "Search URL: $SEARCH_URL"
echo "Query: $QUERY"
echo ""

# Test people search
echo "----------------------------------------"
echo "Testing /search/people endpoint"
echo "----------------------------------------"
echo "Request: GET $SEARCH_URL/search/people?q=$QUERY"
echo ""
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$SEARCH_URL/search/people?q=$QUERY")
HTTP_STATUS=$(echo "$RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

echo "HTTP Status: $HTTP_STATUS"
echo "Response Body:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

# Test property search
# echo "----------------------------------------"
# echo "Testing /search/property endpoint"
# echo "----------------------------------------"
# echo "Request: GET $SEARCH_URL/search/property?q=$QUERY"
# echo ""
# RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" "$SEARCH_URL/search/property?q=$QUERY")
# HTTP_STATUS=$(echo "$RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
# BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

# echo "HTTP Status: $HTTP_STATUS"
# echo "Response Body:"
# echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
# echo ""

echo "=========================================="
echo "Test Complete"
echo "=========================================="

