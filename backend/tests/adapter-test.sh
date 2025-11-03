#!/bin/bash

# Adapter Service Test Script
# Tests the adapter service chat endpoint: /api/chat

ADAPTER_URL="${ADAPTER_URL:-http://localhost:8080}"
AGENT_ID="${1:-agent-123}"
MESSAGE="${2:-Show me recent sales in the Inner West.}"

echo "=========================================="
echo "Adapter Service Test"
echo "=========================================="
echo "Adapter URL: $ADAPTER_URL"
echo "Agent ID: $AGENT_ID"
echo "Message: $MESSAGE"
echo ""

# Prepare JSON payload
PAYLOAD=$(jq -n \
  --arg agentId "$AGENT_ID" \
  --arg message "$MESSAGE" \
  '{agentId: $agentId, message: $message}')

echo "----------------------------------------"
echo "Testing /api/chat endpoint"
echo "----------------------------------------"
echo "Request: POST $ADAPTER_URL/api/chat"
echo "Payload:"
echo "$PAYLOAD" | jq '.'
echo ""

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  "$ADAPTER_URL/api/chat")

HTTP_STATUS=$(echo "$RESPONSE" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

echo "HTTP Status: $HTTP_STATUS"
echo "Response Body:"
echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
echo ""

echo "=========================================="
echo "Test Complete"
echo "=========================================="

