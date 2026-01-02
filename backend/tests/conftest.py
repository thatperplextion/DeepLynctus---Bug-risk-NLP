"""
Test Configuration
pytest configuration and fixtures
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.db import get_database


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database fixture"""
    from backend.services.db import InMemoryDB
    return InMemoryDB()


@pytest.fixture
def sample_project_data():
    """Sample project data for testing"""
    return {
        "project_id": "test_project_123",
        "files": [
            {
                "path": "src/main.py",
                "risk_score": 0.85,
                "complexity": 25,
                "issues": [
                    {
                        "type": "security",
                        "severity": "critical",
                        "message": "SQL injection vulnerability"
                    }
                ]
            },
            {
                "path": "src/utils.py",
                "risk_score": 0.32,
                "complexity": 8,
                "issues": []
            }
        ]
    }


@pytest.fixture
def auth_headers():
    """Auth headers for testing"""
    return {
        "Authorization": "Bearer test_token_123"
    }
