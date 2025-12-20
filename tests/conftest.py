"""Test configuration and fixtures."""

import os
import pytest


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    """Set up environment for tests."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
    monkeypatch.setenv("ENABLE_MOCK_MODE", "true")


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    from coding_swarm.models import SwarmConfig

    return SwarmConfig(
        gemini_api_key="test-api-key",
        enable_mock_mode=True,
    )


@pytest.fixture
def sample_code():
    """Sample Python code for testing."""
    return '''"""Sample module."""


def greet(name: str) -> str:
    """Greet someone by name.

    Args:
        name: The name to greet

    Returns:
        Greeting message
    """
    return f"Hello, {name}!"


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


class Calculator:
    """Simple calculator class."""

    def multiply(self, x: int, y: int) -> int:
        """Multiply two numbers."""
        return x * y
'''


@pytest.fixture
def sample_code_without_docstrings():
    """Sample Python code without docstrings."""
    return """def greet(name):
    return f"Hello, {name}!"


def add(a, b):
    return a + b
"""


@pytest.fixture
def sample_code_with_syntax_error():
    """Sample Python code with syntax error."""
    return """def broken_function(
    return "missing closing paren"
"""
