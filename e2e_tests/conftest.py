"""
Pytest configuration and fixtures for e2e tests.
"""

import pytest
from things3.things3_api import Things3API


@pytest.fixture(scope="session")
def api():
    """
    Create a Things3API instance for testing.
    
    This fixture has session scope to reuse the same API instance
    across all tests in the session.
    """
    return Things3API()


@pytest.fixture(scope="function")
def test_todo_id():
    """
    Placeholder for test todo ID that can be used across test functions.
    This will be set by the create test and used by update test.
    """
    return None