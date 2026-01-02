"""
Integration Tests for API Endpoints
"""

import pytest
from fastapi import status


@pytest.mark.asyncio
async def test_register_user(client):
    """Test user registration endpoint"""
    response = client.post(
        "/users/auth/register",
        json={
            "email": "test@example.com",
            "password": "SecurePass123",
            "username": "testuser",
            "organization": "Test Org"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "session_id" in data


@pytest.mark.asyncio
async def test_search_endpoint(client, auth_headers):
    """Test advanced search endpoint"""
    response = client.post(
        "/search/test_project",
        headers=auth_headers,
        json={
            "query": "test",
            "filters": {
                "severity": ["high", "critical"],
                "risk_score_min": 50
            }
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "results" in data


@pytest.mark.asyncio
async def test_security_scan_endpoint(client, auth_headers):
    """Test security scanning endpoint"""
    response = client.get(
        "/security/test_project/secrets",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "secrets" in data


@pytest.mark.asyncio
async def test_analytics_endpoint(client, auth_headers):
    """Test analytics endpoint"""
    response = client.get(
        "/analytics/test_project/productivity?days=30",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "files_improved" in data


@pytest.mark.asyncio
async def test_notification_subscribe(client, auth_headers):
    """Test notification subscription"""
    response = client.post(
        "/notifications/subscribe",
        headers=auth_headers,
        json={
            "user_id": "test_user",
            "project_id": "test_project",
            "channels": ["email"],
            "config": {"email": "test@example.com"}
        }
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_integration_setup(client, auth_headers):
    """Test GitHub integration setup"""
    response = client.post(
        "/integrations/test_project/github",
        headers=auth_headers,
        json={
            "repo_name": "test/repo",
            "access_token": "test_token"
        }
    )
    assert response.status_code == status.HTTP_200_OK
