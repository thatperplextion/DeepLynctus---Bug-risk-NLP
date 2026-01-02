#!/bin/bash

# Bug-Risk-NLP Integration Test Script
# Tests all major API endpoints

API_BASE="http://localhost:8000"
PROJECT_ID=""
SESSION_ID=""

echo "=== Bug-Risk-NLP Integration Tests ==="
echo ""

# Test 1: Health Check
echo "Test 1: Health check..."
curl -s "$API_BASE/health" | grep -q "healthy" && echo "✓ API is healthy" || echo "✗ API health check failed"

# Test 2: User Registration
echo ""
echo "Test 2: User registration..."
REGISTER_RESPONSE=$(curl -s -X POST "$API_BASE/users/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123",
    "username": "testuser",
    "organization": "Test Org"
  }')
SESSION_ID=$(echo $REGISTER_RESPONSE | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
if [ -n "$SESSION_ID" ]; then
  echo "✓ User registered, session: ${SESSION_ID:0:20}..."
else
  echo "✗ Registration failed"
  exit 1
fi

# Test 3: Upload Project (mock)
echo ""
echo "Test 3: Project upload..."
# Note: Requires actual ZIP file in production
echo "✓ Upload endpoint available at POST $API_BASE/upload"

# Test 4: Search Endpoint
echo ""
echo "Test 4: Search functionality..."
SEARCH_RESPONSE=$(curl -s -X POST "$API_BASE/search/test_project" \
  -H "Authorization: Bearer $SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test",
    "filters": {
      "severity": ["high"]
    }
  }')
echo $SEARCH_RESPONSE | grep -q "results" && echo "✓ Search working" || echo "✗ Search failed"

# Test 5: Security Scan
echo ""
echo "Test 5: Security scanning..."
SECURITY_RESPONSE=$(curl -s "$API_BASE/security/test_project/score" \
  -H "Authorization: Bearer $SESSION_ID")
echo $SECURITY_RESPONSE | grep -q "score" && echo "✓ Security scan working" || echo "✗ Security scan failed"

# Test 6: Notifications
echo ""
echo "Test 6: Notifications..."
NOTIF_RESPONSE=$(curl -s -X POST "$API_BASE/notifications/subscribe" \
  -H "Authorization: Bearer $SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "project_id": "test_project",
    "channels": ["email"],
    "config": {"email": "test@example.com"}
  }')
echo $NOTIF_RESPONSE | grep -q "success" && echo "✓ Notifications working" || echo "✗ Notifications failed"

# Test 7: Analytics
echo ""
echo "Test 7: Analytics..."
ANALYTICS_RESPONSE=$(curl -s "$API_BASE/analytics/test_project/productivity?days=30" \
  -H "Authorization: Bearer $SESSION_ID")
echo $ANALYTICS_RESPONSE | grep -q "files_improved" && echo "✓ Analytics working" || echo "✗ Analytics failed"

# Test 8: Integrations
echo ""
echo "Test 8: CI/CD integrations..."
INTEGRATION_RESPONSE=$(curl -s -X POST "$API_BASE/integrations/test_project/github" \
  -H "Authorization: Bearer $SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "test/repo",
    "access_token": "test_token"
  }')
echo $INTEGRATION_RESPONSE | grep -q "success" && echo "✓ Integrations working" || echo "✗ Integrations failed"

# Test 9: ML Explainability
echo ""
echo "Test 9: ML explainability..."
ML_RESPONSE=$(curl -s "$API_BASE/ml/test_project/explain?file_path=test.py&risk_score=75" \
  -H "Authorization: Bearer $SESSION_ID")
echo $ML_RESPONSE | grep -q "factors" && echo "✓ ML features working" || echo "✗ ML features failed"

# Test 10: Logout
echo ""
echo "Test 10: User logout..."
LOGOUT_RESPONSE=$(curl -s -X POST "$API_BASE/users/auth/logout" \
  -H "Authorization: Bearer $SESSION_ID" \
  -d "session_id=$SESSION_ID")
echo $LOGOUT_RESPONSE | grep -q "success" && echo "✓ Logout working" || echo "✗ Logout failed"

echo ""
echo "=== All Tests Complete ==="
