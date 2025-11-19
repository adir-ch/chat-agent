#!/bin/bash

# Profile Service Test Script
# Tests the profile service profile endpoint: GET /api/profile/{agentId}

PROFILE_URL="${PROFILE_URL:-http://localhost:8080}"
AGENT_ID="${1:-agent-123}"

echo "=========================================="
echo "Profile Service Test"
echo "=========================================="
echo "Profile URL: $PROFILE_URL"
echo "Agent ID: $AGENT_ID"
echo ""

echo "----------------------------------------"
echo "Testing /api/profile/{agentId} endpoint"
echo "----------------------------------------"
echo "Request: GET $PROFILE_URL/api/profile/$AGENT_ID"
echo ""

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -X GET \
  -H "Content-Type: application/json" \
  "$PROFILE_URL/api/profile/$AGENT_ID")

HTTP_STATUS=$(echo "$RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

echo "HTTP Status: $HTTP_STATUS"
echo "Response Body:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

echo "=========================================="
echo "Test Complete"
echo "=========================================="

