#!/bin/bash

# Agent Service Test Script
# Tests the agent service chat endpoint: POST /chat

AGENT_URL="${AGENT_URL:-http://localhost:8070}"
AGENT_ID="${1:-agent-123}"
MESSAGE="${2:-Show me properties in Newtown}"

echo "=========================================="
echo "Agent Service Test"
echo "=========================================="
echo "Agent URL: $AGENT_URL"
echo "Agent ID: $AGENT_ID"
echo "Message: $MESSAGE"
echo ""

echo "----------------------------------------"
echo "Testing /chat endpoint"
echo "----------------------------------------"
echo "Request: POST $AGENT_URL/chat"
echo "Body: {\"agentId\":\"$AGENT_ID\",\"message\":\"$MESSAGE\"}"
echo ""

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d "{\"agentId\":\"$AGENT_ID\",\"message\":\"$MESSAGE\"}" \
  "$AGENT_URL/chat")

HTTP_STATUS=$(echo "$RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

echo "HTTP Status: $HTTP_STATUS"
echo "Response Body:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

echo "=========================================="
echo "Test Complete"
echo "=========================================="

