#!/bin/bash
# Testing script for FastAPI backend

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== PeopleFinder FastAPI Backend Test ===${NC}\n"

# Test 1: Health Check
echo -e "${YELLOW}Test 1: Health Check${NC}"
echo "GET /health"
curl -s http://localhost:3001/health | python3 -m json.tool
echo -e "\n"

# Test 2: Root Endpoint
echo -e "${YELLOW}Test 2: Root Endpoint${NC}"
echo "GET /"
curl -s http://localhost:3001/ | python3 -m json.tool
echo -e "\n"

# Test 3: Chat Endpoint (Streaming)
echo -e "${YELLOW}Test 3: Chat Endpoint (Streaming)${NC}"
echo "POST /api/chat"
echo "Query: 'Find information about Elon Musk'"
echo ""
echo "Response (first 5 lines):"
curl -N -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Find information about Elon Musk"}' \
  2>/dev/null | head -5
echo ""
echo -e "${GREEN}✓ Streaming enabled (press Ctrl+C to stop)${NC}\n"

# Test 4: Invalid Request
echo -e "${YELLOW}Test 4: Invalid Request (missing query)${NC}"
echo "POST /api/chat (no query)"
curl -s -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool
echo -e "\n"

# Test 5: OpenAPI Documentation
echo -e "${YELLOW}Test 5: OpenAPI Documentation${NC}"
echo "GET /docs"
echo "Available at: http://localhost:3001/docs"
echo "Alternative: http://localhost:3001/redoc"
echo -e "\n"

echo -e "${GREEN}=== Tests Complete ===${NC}"
echo ""
echo "To run a full streaming test, try:"
echo "curl -N -X POST http://localhost:3001/api/chat \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"query\": \"Your search query here\"}'"
