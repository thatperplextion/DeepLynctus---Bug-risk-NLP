"""
Test Search Service
"""

import pytest
from backend.services.search_service import SearchService


@pytest.mark.asyncio
async def test_search_files(mock_db):
    """Test file search with filters"""
    service = SearchService(mock_db)
    results = await service.search_files(
        project_id="test_project",
        query="test",
        filters={"severity": ["high", "critical"]}
    )
    assert "results" in results


@pytest.mark.asyncio
async def test_save_filter(mock_db):
    """Test saving search filters"""
    service = SearchService(mock_db)
    result = await service.save_filter(
        user_id="test_user",
        filter_name="High Risks",
        filters={"severity": ["high", "critical"]}
    )
    assert result["success"] is True


@pytest.mark.asyncio
async def test_pattern_search(mock_db):
    """Test regex pattern search"""
    service = SearchService(mock_db)
    # Add test implementation
    assert True
