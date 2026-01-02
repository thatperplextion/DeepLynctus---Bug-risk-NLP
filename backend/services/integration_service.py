"""
Integration Service
Handles GitHub Actions, GitLab CI/CD, Jira, and Webhook integrations
"""

from typing import Dict, List, Optional
import json


class IntegrationService:
    """Manages external integrations"""
    
    def __init__(self, db):
        self.db = db
        self.integrations = {}
    
    async def setup_github_integration(self, project_id: str, repo_url: str,
                                      access_token: str) -> Dict:
        """Setup GitHub Actions integration"""
        integration = {
            "type": "github",
            "project_id": project_id,
            "repo_url": repo_url,
            "access_token": access_token,
            "enabled": True,
            "config": {
                "run_on_pr": True,
                "run_on_push": True,
                "branches": ["main", "develop"]
            }
        }
        
        self.integrations[f"github_{project_id}"] = integration
        
        return {
            "status": "github_integration_setup",
            "workflow_file": self._generate_github_workflow()
        }
    
    def _generate_github_workflow(self) -> str:
        """Generate GitHub Actions workflow file"""
        workflow = """name: Bug Risk NLP Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Bug Risk Analysis
        run: |
          curl -X POST "${{ secrets.BUGRISK_API_URL }}/scan/${{ secrets.PROJECT_ID }}" \\
            -H "Authorization: Bearer ${{ secrets.BUGRISK_API_KEY }}" \\
            -F "repository=@./"
      
      - name: Check Quality Gate
        run: |
          QUALITY_SCORE=$(curl "${{ secrets.BUGRISK_API_URL }}/metrics/${{ secrets.PROJECT_ID }}" | jq '.quality_score')
          if [ "$QUALITY_SCORE" -lt "70" ]; then
            echo "Quality score below threshold: $QUALITY_SCORE"
            exit 1
          fi
"""
        return workflow
    
    async def setup_gitlab_integration(self, project_id: str, repo_url: str,
                                      access_token: str) -> Dict:
        """Setup GitLab CI/CD integration"""
        integration = {
            "type": "gitlab",
            "project_id": project_id,
            "repo_url": repo_url,
            "access_token": access_token,
            "enabled": True
        }
        
        self.integrations[f"gitlab_{project_id}"] = integration
        
        return {
            "status": "gitlab_integration_setup",
            "ci_file": self._generate_gitlab_ci()
        }
    
    def _generate_gitlab_ci(self) -> str:
        """Generate GitLab CI configuration"""
        ci_config = """stages:
  - analyze

bug_risk_analysis:
  stage: analyze
  image: python:3.10
  script:
    - pip install requests
    - python -c "import requests; requests.post('$BUGRISK_API_URL/scan/$PROJECT_ID', headers={'Authorization': 'Bearer $API_KEY'}, files={'repository': open('./', 'rb')})"
  only:
    - main
    - develop
"""
        return ci_config
    
    async def setup_jira_integration(self, project_id: str, jira_url: str,
                                    project_key: str, api_token: str) -> Dict:
        """Setup Jira integration for auto-ticket creation"""
        integration = {
            "type": "jira",
            "project_id": project_id,
            "jira_url": jira_url,
            "project_key": project_key,
            "api_token": api_token,
            "enabled": True,
            "config": {
                "create_tickets_for": ["critical", "high"],
                "issue_type": "Bug",
                "priority_mapping": {
                    "critical": "Highest",
                    "high": "High",
                    "medium": "Medium"
                }
            }
        }
        
        self.integrations[f"jira_{project_id}"] = integration
        
        return {"status": "jira_integration_setup"}
    
    async def create_jira_ticket(self, integration_key: str, issue: Dict) -> Dict:
        """Create a Jira ticket for a code issue"""
        integration = self.integrations.get(integration_key)
        
        if not integration or integration["type"] != "jira":
            raise ValueError("Jira integration not found")
        
        ticket = {
            "summary": f"Code Quality Issue: {issue.get('file', 'Unknown')}",
            "description": issue.get('message', 'No description'),
            "priority": integration["config"]["priority_mapping"].get(
                issue.get('severity', 'medium'), "Medium"
            ),
            "issuetype": integration["config"]["issue_type"],
            "project": {"key": integration["project_key"]}
        }
        
        # TODO: Actual Jira API call
        print(f"📝 Would create Jira ticket: {ticket}")
        
        return {"status": "ticket_created", "ticket": ticket}
    
    async def setup_webhook(self, project_id: str, webhook_url: str,
                           events: List[str]) -> Dict:
        """Setup webhook for external notifications"""
        integration = {
            "type": "webhook",
            "project_id": project_id,
            "webhook_url": webhook_url,
            "events": events,
            "enabled": True
        }
        
        self.integrations[f"webhook_{project_id}"] = integration
        
        return {"status": "webhook_setup", "events": events}
    
    async def trigger_webhook(self, project_id: str, event: str, data: Dict) -> Dict:
        """Trigger webhook for an event"""
        webhook_key = f"webhook_{project_id}"
        integration = self.integrations.get(webhook_key)
        
        if not integration or event not in integration["events"]:
            return {"status": "webhook_not_triggered"}
        
        payload = {
            "event": event,
            "project_id": project_id,
            "timestamp": json.dumps(data),
            "data": data
        }
        
        # TODO: Actual HTTP POST to webhook URL
        print(f"🔗 Webhook triggered: {integration['webhook_url']}")
        
        return {"status": "webhook_triggered", "payload": payload}
