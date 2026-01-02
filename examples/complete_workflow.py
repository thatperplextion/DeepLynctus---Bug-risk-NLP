"""
Complete Python Example: Automated Security Monitoring Pipeline

This script demonstrates a complete workflow:
1. Upload and scan a project
2. Check security score
3. Setup notifications
4. Monitor for issues
5. Generate reports
"""

import requests
import time
import json
from typing import Dict, List


class BugRiskClient:
    """Client for Bug-Risk-NLP API"""
    
    def __init__(self, api_base: str = "http://localhost:8000"):
        self.api_base = api_base
        self.session_id = None
        self.headers = {}
    
    def register(self, email: str, password: str, username: str, org: str) -> Dict:
        """Register a new user"""
        response = requests.post(f"{self.api_base}/users/auth/register", json={
            "email": email,
            "password": password,
            "username": username,
            "organization": org
        })
        response.raise_for_status()
        data = response.json()
        self.session_id = data["session_id"]
        self.headers = {"Authorization": f"Bearer {self.session_id}"}
        return data
    
    def login(self, email: str, password: str) -> Dict:
        """Login existing user"""
        response = requests.post(f"{self.api_base}/users/auth/login", json={
            "email": email,
            "password": password
        })
        response.raise_for_status()
        data = response.json()
        self.session_id = data["session_id"]
        self.headers = {"Authorization": f"Bearer {self.session_id}"}
        return data
    
    def upload_project(self, zip_path: str) -> str:
        """Upload project ZIP file"""
        with open(zip_path, 'rb') as f:
            files = {'file': (zip_path, f, 'application/zip')}
            response = requests.post(f"{self.api_base}/upload", files=files)
            response.raise_for_status()
            return response.json()["project_id"]
    
    def scan_project(self, project_id: str) -> Dict:
        """Get scan results"""
        response = requests.get(f"{self.api_base}/scan/{project_id}")
        response.raise_for_status()
        return response.json()
    
    def get_security_score(self, project_id: str) -> Dict:
        """Get security score"""
        response = requests.get(
            f"{self.api_base}/security/{project_id}/score",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_secrets(self, project_id: str) -> List[Dict]:
        """Scan for exposed secrets"""
        response = requests.get(
            f"{self.api_base}/security/{project_id}/secrets",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()["secrets"]
    
    def get_vulnerabilities(self, project_id: str) -> List[Dict]:
        """Scan for vulnerabilities"""
        response = requests.get(
            f"{self.api_base}/security/{project_id}/vulnerabilities",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()["vulnerabilities"]
    
    def subscribe_notifications(self, user_id: str, project_id: str, 
                               email: str, slack_webhook: str = None) -> Dict:
        """Setup notifications"""
        channels = ["email"]
        config = {"email": email}
        
        if slack_webhook:
            channels.append("slack")
            config["slack_webhook"] = slack_webhook
        
        response = requests.post(
            f"{self.api_base}/notifications/subscribe",
            headers=self.headers,
            json={
                "user_id": user_id,
                "project_id": project_id,
                "channels": channels,
                "config": config,
                "triggers": {
                    "on_critical_issue": True,
                    "on_regression": True,
                    "on_scan_complete": True
                }
            }
        )
        response.raise_for_status()
        return response.json()
    
    def search_files(self, project_id: str, query: str, filters: Dict = None) -> List[Dict]:
        """Search files with filters"""
        response = requests.post(
            f"{self.api_base}/search/{project_id}",
            headers=self.headers,
            json={
                "query": query,
                "filters": filters or {}
            }
        )
        response.raise_for_status()
        return response.json()["results"]
    
    def get_analytics(self, project_id: str, days: int = 30) -> Dict:
        """Get productivity analytics"""
        response = requests.get(
            f"{self.api_base}/analytics/{project_id}/productivity",
            params={"days": days},
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def generate_report(self, project_id: str, title: str, sections: List[Dict]) -> Dict:
        """Generate custom report"""
        response = requests.post(
            f"{self.api_base}/reports/custom",
            headers=self.headers,
            json={
                "project_id": project_id,
                "title": title,
                "sections": sections,
                "format": "pdf"
            }
        )
        response.raise_for_status()
        return response.json()


def main():
    """Main workflow"""
    client = BugRiskClient("http://localhost:8000")
    
    print("=== Bug-Risk-NLP Security Monitoring Pipeline ===\n")
    
    # Step 1: Authentication
    print("Step 1: Authenticating...")
    try:
        client.login("dev@company.com", "SecurePass123")
        print("✓ Logged in successfully")
    except:
        print("Creating new account...")
        client.register(
            email="dev@company.com",
            password="SecurePass123",
            username="developer",
            org="My Company"
        )
        print("✓ Account created")
    
    # Step 2: Upload project
    print("\nStep 2: Uploading project...")
    project_id = client.upload_project("myproject.zip")
    print(f"✓ Project uploaded: {project_id}")
    
    # Step 3: Wait for scan to complete
    print("\nStep 3: Scanning project...")
    time.sleep(5)  # Wait for scan
    scan_results = client.scan_project(project_id)
    print(f"✓ Scan complete")
    print(f"  Risk Score: {scan_results['overall_risk_score']}")
    print(f"  Critical Issues: {scan_results['critical_issues_count']}")
    
    # Step 4: Security analysis
    print("\nStep 4: Security analysis...")
    
    # Check security score
    security_score = client.get_security_score(project_id)
    print(f"  Security Score: {security_score['score']}/100 (Grade: {security_score['grade']})")
    
    # Scan for secrets
    secrets = client.get_secrets(project_id)
    if secrets:
        print(f"  ⚠️ Found {len(secrets)} exposed secrets!")
        for secret in secrets[:3]:  # Show first 3
            print(f"    - {secret['type']} in {secret['file']}")
    else:
        print("  ✓ No exposed secrets found")
    
    # Scan for vulnerabilities
    vulnerabilities = client.get_vulnerabilities(project_id)
    if vulnerabilities:
        print(f"  ⚠️ Found {len(vulnerabilities)} vulnerabilities!")
        for vuln in vulnerabilities[:3]:  # Show first 3
            print(f"    - {vuln['type']} in {vuln['file']}")
    else:
        print("  ✓ No vulnerabilities found")
    
    # Step 5: Setup notifications
    print("\nStep 5: Setting up notifications...")
    client.subscribe_notifications(
        user_id="user123",
        project_id=project_id,
        email="dev@company.com",
        slack_webhook="https://hooks.slack.com/services/YOUR/WEBHOOK"
    )
    print("✓ Notifications configured")
    
    # Step 6: Search for high-risk files
    print("\nStep 6: Searching for high-risk files...")
    high_risk_files = client.search_files(
        project_id,
        query="",
        filters={
            "severity": ["high", "critical"],
            "risk_score_min": 70
        }
    )
    print(f"  Found {len(high_risk_files)} high-risk files")
    for file in high_risk_files[:5]:
        print(f"    - {file['file_path']}: {file['risk_score']}")
    
    # Step 7: Get analytics
    print("\nStep 7: Team analytics...")
    analytics = client.get_analytics(project_id, days=30)
    print(f"  Files Improved: {analytics.get('files_improved', 0)}")
    print(f"  Issues Fixed: {analytics.get('issues_fixed', 0)}")
    print(f"  Improvement Rate: {analytics.get('improvement_rate', 0)}%")
    
    # Step 8: Generate report
    print("\nStep 8: Generating security report...")
    report = client.generate_report(
        project_id,
        title="Security Assessment Report",
        sections=[
            {"type": "executive_summary"},
            {"type": "security_overview"},
            {"type": "top_risks", "limit": 10},
            {"type": "recommendations"}
        ]
    )
    print(f"✓ Report generated: {report.get('download_url', 'N/A')}")
    
    print("\n=== Pipeline Complete ===")
    print(f"\nProject Dashboard: http://localhost:3000/projects/{project_id}")
    print(f"Security Score: {security_score['score']}/100")
    print(f"Action Required: {'Yes' if secrets or vulnerabilities else 'No'}")


if __name__ == "__main__":
    main()
