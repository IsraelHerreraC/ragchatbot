"""
Pytest configuration and shared fixtures for RAG system tests.
"""

import sys
from pathlib import Path

# Add backend directory to Python path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock

import pytest

# Import models for creating test data
from models import Course, CourseChunk, Lesson
from vector_store import SearchResults


@pytest.fixture
def sample_course():
    """Create a sample course for testing."""
    return Course(
        title="Introduction to Machine Learning",
        course_link="https://example.com/ml-course",
        instructor="Dr. Jane Smith",
        lessons=[
            Lesson(
                lesson_number=0,
                title="Introduction",
                lesson_link="https://example.com/ml-course/lesson-0",
            ),
            Lesson(
                lesson_number=1,
                title="Supervised Learning",
                lesson_link="https://example.com/ml-course/lesson-1",
            ),
            Lesson(
                lesson_number=2,
                title="Unsupervised Learning",
                lesson_link="https://example.com/ml-course/lesson-2",
            ),
        ],
    )


@pytest.fixture
def sample_course_chunks():
    """Create sample course chunks for testing."""
    return [
        CourseChunk(
            content="Introduction to machine learning concepts and terminology.",
            course_title="Introduction to Machine Learning",
            lesson_number=0,
            chunk_index=0,
        ),
        CourseChunk(
            content="Supervised learning involves training models with labeled data.",
            course_title="Introduction to Machine Learning",
            lesson_number=1,
            chunk_index=1,
        ),
        CourseChunk(
            content="Common supervised learning algorithms include linear regression and decision trees.",
            course_title="Introduction to Machine Learning",
            lesson_number=1,
            chunk_index=2,
        ),
    ]


@pytest.fixture
def sample_search_results():
    """Create sample search results for testing."""
    return SearchResults(
        documents=[
            "Introduction to machine learning concepts and terminology.",
            "Supervised learning involves training models with labeled data.",
        ],
        metadata=[
            {
                "course_title": "Introduction to Machine Learning",
                "lesson_number": 0,
                "chunk_index": 0,
            },
            {
                "course_title": "Introduction to Machine Learning",
                "lesson_number": 1,
                "chunk_index": 1,
            },
        ],
        distances=[0.1, 0.2],
        error=None,
    )


@pytest.fixture
def empty_search_results():
    """Create empty search results for testing."""
    return SearchResults(documents=[], metadata=[], distances=[], error=None)


@pytest.fixture
def error_search_results():
    """Create search results with error for testing."""
    return SearchResults.empty("Search error: Database connection failed")


@pytest.fixture
def mock_vector_store():
    """Create a mock VectorStore for testing."""
    mock_store = Mock()
    mock_store.search = Mock()
    mock_store._resolve_course_name = Mock()
    mock_store.get_lesson_link = Mock()
    mock_store.course_catalog = Mock()
    return mock_store


@pytest.fixture
def mock_tool_manager():
    """Create a mock ToolManager for testing."""
    mock_manager = Mock()
    mock_manager.execute_tool = Mock()
    mock_manager.get_tool_definitions = Mock(return_value=[])
    mock_manager.get_last_sources = Mock(return_value=[])
    mock_manager.reset_sources = Mock()
    return mock_manager


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic API client for testing."""
    mock_client = Mock()
    mock_client.messages = Mock()
    mock_client.messages.create = Mock()
    return mock_client


@pytest.fixture
def mock_session_manager():
    """Create a mock SessionManager for testing."""
    mock_manager = Mock()
    mock_manager.create_session = Mock(return_value="session_1")
    mock_manager.add_exchange = Mock()
    mock_manager.get_conversation_history = Mock(return_value=None)
    return mock_manager


@pytest.fixture
def sample_anthropic_text_response():
    """Create a sample Anthropic text response (no tool use)."""
    mock_response = Mock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [
        Mock(type="text", text="This is a sample response from the AI.")
    ]
    return mock_response


@pytest.fixture
def sample_anthropic_tool_use_response():
    """Create a sample Anthropic response with tool use."""
    # Mock tool use block
    tool_block = Mock()
    tool_block.type = "tool_use"
    tool_block.id = "tool_call_123"
    tool_block.name = "search_course_content"
    tool_block.input = {"query": "machine learning basics"}

    mock_response = Mock()
    mock_response.stop_reason = "tool_use"
    mock_response.content = [tool_block]
    return mock_response


@pytest.fixture
def sample_anthropic_final_response():
    """Create a sample Anthropic final response after tool execution."""
    mock_response = Mock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [
        Mock(type="text", text="Based on the search results, machine learning is...")
    ]
    return mock_response
