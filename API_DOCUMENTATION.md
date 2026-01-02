# API Documentation - Bug Risk NLP

## Authentication Endpoints

### POST /users/auth/register
Register a new user account

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "John Doe",
  "organization": "Acme Corp"
}
```

### POST /users/auth/login
Authenticate user and get session token

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

## Notification Endpoints

### POST /notifications/subscribe
Subscribe to project notifications

**Request Body:**
```json
{
  "project_id": "proj_123",
  "user_id": "user_456",
  "channels": ["email", "slack"],
  "notification_types": ["critical_issue", "scan_complete"]
}
```

### GET /notifications/{user_id}
Get user notifications

**Query Parameters:**
- `project_id` (optional): Filter by project
- `unread_only` (optional): Show only unread

## Search Endpoints

### POST /search/{project_id}
Advanced search with filters

**Request Body:**
```json
{
  "query": "authentication",
  "filters": {
    "severity": ["critical", "high"],
    "min_risk_score": 0.6,
    "file_types": ["python", "javascript"]
  }
}
```

### POST /search/{project_id}/pattern
Regex pattern search

**Query Parameters:**
- `pattern`: Regex pattern
- `regex`: Boolean (default: false)

## Security Endpoints

### GET /security/{project_id}/secrets
Scan for exposed secrets (API keys, passwords, tokens)

### GET /security/{project_id}/vulnerabilities
Scan for OWASP Top 10 vulnerabilities

### GET /security/{project_id}/score
Get overall security score and grade

## Analytics Endpoints

### GET /analytics/{project_id}/productivity
Get team productivity metrics

**Query Parameters:**
- `days`: Time period (default: 30)

**Response:**
```json
{
  "files_improved": 45,
  "files_degraded": 5,
  "total_issues_fixed": 128,
  "improvement_rate": 89.5
}
```

### GET /analytics/{project_id}/cost-savings
Calculate cost savings from bug prevention

**Response:**
```json
{
  "total_cost_savings": 125000,
  "developer_hours_saved": 320,
  "breakdown": {
    "critical_bugs_prevented": 12,
    "high_bugs_prevented": 38,
    "medium_bugs_prevented": 78
  }
}
```

### GET /analytics/{project_id}/technology-heatmap
Analyze which technologies have highest risk

## Integration Endpoints

### POST /integrations/{project_id}/github
Setup GitHub Actions integration

**Request Body:**
```json
{
  "repo_url": "https://github.com/user/repo",
  "access_token": "ghp_..."
}
```

### POST /integrations/{project_id}/jira
Setup Jira integration for auto-ticket creation

**Request Body:**
```json
{
  "jira_url": "https://company.atlassian.net",
  "project_key": "PROJ",
  "api_token": "token123"
}
```

## Performance Endpoints

### POST /performance/{project_id}/incremental-scan
Perform incremental scan (only changed files)

**Request Body:**
```json
{
  "files": ["src/main.py", "src/utils.py"]
}
```

### GET /performance/{project_id}/metrics-cached
Get cached metrics for faster dashboard loads

## ML Enhancement Endpoints

### GET /ml/{project_id}/explain
Explain why a file has a specific risk score

**Query Parameters:**
- `file_path`: Path to file
- `risk_score`: Risk score to explain

### POST /ml/{project_id}/threshold
Set custom risk thresholds

**Request Body:**
```json
{
  "risk_level": "high",
  "threshold": 0.75
}
```

### GET /ml/{project_id}/anomalies
Detect unusual code patterns

### POST /ml/{project_id}/learn
Learn patterns from project history

## Comparison Endpoints

### GET /comparison/{project_id}/history
Get scan history

### GET /comparison/{project_id}/compare
Compare two scans

**Query Parameters:**
- `scan1_id`: First scan ID
- `scan2_id`: Second scan ID

### GET /comparison/{project_id}/timeline
Get quality timeline

**Query Parameters:**
- `days`: Time period (default: 30)

### GET /comparison/{project_id}/roi
Get ROI metrics

## Rate Limiting

API requests are limited to:
- **Free tier**: 100 requests/hour
- **Pro tier**: 1000 requests/hour
- **Enterprise**: Unlimited

## Error Codes

- `400`: Bad Request - Invalid parameters
- `401`: Unauthorized - Invalid or missing authentication
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource doesn't exist
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error - Server error

## Webhooks

Configure webhooks to receive real-time notifications:

**Webhook Payload:**
```json
{
  "event": "scan_complete",
  "project_id": "proj_123",
  "timestamp": "2026-01-02T10:30:00Z",
  "data": {
    "quality_score": 85,
    "critical_files": 3
  }
}
```

**Available Events:**
- `scan_complete`
- `critical_issue_found`
- `quality_improved`
- `quality_degraded`
- `security_issue_found`
