# Bug-Risk-NLP Usage Examples

This directory contains practical examples for using the Bug-Risk-NLP platform.

## Quick Start Examples

### 1. Basic Code Scanning

```python
import requests

API_BASE = "http://localhost:8000"

# Upload and scan a project
files = {
    'file': ('myproject.zip', open('myproject.zip', 'rb'), 'application/zip')
}
response = requests.post(f"{API_BASE}/upload", files=files)
project_id = response.json()["project_id"]

# Get scan results
results = requests.get(f"{API_BASE}/scan/{project_id}").json()
print(f"Risk Score: {results['overall_risk_score']}")
print(f"Critical Issues: {results['critical_issues_count']}")
```

### 2. Authentication and Team Setup

```python
# Register a new user
response = requests.post(f"{API_BASE}/users/auth/register", json={
    "email": "dev@company.com",
    "password": "SecurePass123",
    "username": "developer",
    "organization": "My Company"
})
session_id = response.json()["session_id"]

# Create a team
auth_headers = {"Authorization": f"Bearer {session_id}"}
team_response = requests.post(f"{API_BASE}/users/teams", 
    headers=auth_headers,
    json={
        "team_name": "Backend Team",
        "description": "Backend development team"
    }
)
team_id = team_response.json()["team_id"]

# Add team member
requests.post(f"{API_BASE}/users/teams/{team_id}/members",
    headers=auth_headers,
    json={
        "user_id": "other_user_id",
        "role": "developer"
    }
)
```

### 3. Advanced Search with Filters

```python
# Search for high-risk files
search_response = requests.post(f"{API_BASE}/search/{project_id}",
    headers=auth_headers,
    json={
        "query": "authentication",
        "filters": {
            "severity": ["high", "critical"],
            "risk_score_min": 70,
            "file_types": [".py", ".js"]
        }
    }
)

results = search_response.json()["results"]
for file in results:
    print(f"{file['file_path']}: {file['risk_score']}")

# Save filter for reuse
requests.post(f"{API_BASE}/search/filters/save",
    headers=auth_headers,
    json={
        "user_id": "user123",
        "filter_name": "Critical Security Issues",
        "filters": {
            "severity": ["critical"],
            "issue_types": ["security", "vulnerability"]
        }
    }
)
```

### 4. Security Scanning

```python
# Scan for exposed secrets
secrets_response = requests.get(
    f"{API_BASE}/security/{project_id}/secrets",
    headers=auth_headers
)
secrets = secrets_response.json()["secrets"]

for secret in secrets:
    print(f"⚠️ {secret['type']} found in {secret['file']} at line {secret['line']}")

# Get security score
score_response = requests.get(
    f"{API_BASE}/security/{project_id}/score",
    headers=auth_headers
)
print(f"Security Score: {score_response.json()['score']}/100")
print(f"Grade: {score_response.json()['grade']}")
```

### 5. Notifications Setup

```python
# Subscribe to notifications
requests.post(f"{API_BASE}/notifications/subscribe",
    headers=auth_headers,
    json={
        "user_id": "user123",
        "project_id": project_id,
        "channels": ["email", "slack"],
        "config": {
            "email": "dev@company.com",
            "slack_webhook": "https://hooks.slack.com/services/YOUR/WEBHOOK"
        },
        "triggers": {
            "on_critical_issue": True,
            "on_regression": True,
            "on_scan_complete": True
        }
    }
)

# Get notification history
notifications = requests.get(
    f"{API_BASE}/notifications/user123?unread_only=true",
    headers=auth_headers
).json()
```

### 6. CI/CD Integration

```python
# Setup GitHub Actions integration
github_response = requests.post(
    f"{API_BASE}/integrations/{project_id}/github",
    headers=auth_headers,
    json={
        "repo_name": "mycompany/myrepo",
        "access_token": "ghp_xxxxxxxxxxxxx",
        "auto_comment": True,
        "quality_gate": {
            "enabled": True,
            "min_score": 70
        }
    }
)

workflow_yaml = github_response.json()["workflow_yaml"]
print("Add this to .github/workflows/bugrisk.yml:")
print(workflow_yaml)
```

### 7. Team Analytics

```python
# Get team productivity metrics
analytics = requests.get(
    f"{API_BASE}/analytics/{project_id}/productivity?days=30",
    headers=auth_headers
).json()

print(f"Files Improved: {analytics['files_improved']}")
print(f"Issues Fixed: {analytics['issues_fixed']}")
print(f"Improvement Rate: {analytics['improvement_rate']}%")

# Calculate cost savings
savings = requests.get(
    f"{API_BASE}/analytics/{project_id}/cost-savings?days=30",
    headers=auth_headers
).json()

print(f"Total Savings: ${savings['total_savings']}")
print(f"Developer Hours Saved: {savings['hours_saved']}")
```

### 8. ML Model Explainability

```python
# Get risk score explanation
explanation = requests.get(
    f"{API_BASE}/ml/{project_id}/explain",
    params={
        "file_path": "src/auth.py",
        "risk_score": 85
    },
    headers=auth_headers
).json()

print("Risk factors:")
for factor, contribution in explanation["factors"].items():
    print(f"  {factor}: {contribution}%")

# Detect anomalies
anomalies = requests.get(
    f"{API_BASE}/ml/{project_id}/anomalies",
    headers=auth_headers
).json()

for anomaly in anomalies["risk_anomalies"]:
    print(f"Anomaly in {anomaly['file']}: Risk={anomaly['risk_score']}")
```

### 9. Custom Reports

```python
# Create custom report
report = requests.post(f"{API_BASE}/reports/custom",
    headers=auth_headers,
    json={
        "project_id": project_id,
        "title": "Weekly Security Report",
        "sections": [
            {"type": "executive_summary"},
            {"type": "security_overview"},
            {"type": "top_risks", "limit": 10},
            {"type": "trends", "period_days": 7}
        ],
        "format": "pdf"
    }
).json()

# Download report
report_url = report["download_url"]
print(f"Report ready: {report_url}")

# Schedule recurring report
requests.post(f"{API_BASE}/reports/schedule",
    headers=auth_headers,
    json={
        "project_id": project_id,
        "template_id": report["template_id"],
        "frequency": "weekly",
        "day_of_week": "monday",
        "recipients": ["team@company.com"]
    }
)
```

### 10. CLI Tool Usage

```bash
# Install CLI
cd cli
npm install -g .

# Scan project
bugrisk scan /path/to/project --api-url http://localhost:8000

# Get risk score
bugrisk get-score PROJECT_ID --api-url http://localhost:8000

# Generate report
bugrisk report PROJECT_ID --format pdf --output report.pdf
```

## Environment Setup

Create `.env` file with:
```env
# API Configuration
API_BASE_URL=http://localhost:8000
API_KEY=your_api_key_here

# Database
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=bugrisk

# Authentication
JWT_SECRET=your_secret_key

# Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_password

SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK
```

## Best Practices

1. **Always authenticate** before making API calls
2. **Use saved filters** for common search patterns
3. **Enable notifications** for critical issues
4. **Set up CI/CD integration** for automated scanning
5. **Review security scores** regularly
6. **Schedule reports** for stakeholders
7. **Use team features** for collaboration
8. **Monitor analytics** for continuous improvement

## Additional Resources

- API Documentation: `../API_DOCUMENTATION.md`
- Deployment Guide: `../DEPLOYMENT_GUIDE.md`
- Frontend Examples: `./frontend_examples.md`
- Advanced Integrations: `./integrations.md`
