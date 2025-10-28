"""
Tests for CourseSearchTool.execute() method.

This test suite verifies:
- Query execution with various filter combinations
- Error handling for missing courses and empty results
- Source tracking with and without links
- Result formatting
"""
import pytest
from unittest.mock import Mock, patch
from search_tools import CourseSearchTool
from vector_store import SearchResults
from tests.test_helpers import create_search_results, assert_source_format


class TestCourseSearchToolExecute:
    """Tests for CourseSearchTool.execute() method."""

    def test_execute_query_only_success(self, mock_vector_store, sample_search_results):
        """Test successful search with query only (no filters)."""
        # Setup
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = sample_search_results

        # Execute
        result = tool.execute(query="machine learning basics")

        # Verify
        mock_vector_store.search.assert_called_once_with(
            query="machine learning basics",
            course_name=None,
            lesson_number=None
        )
        assert isinstance(result, str)
        assert "Introduction to Machine Learning" in result
        assert "machine learning concepts" in result

    def test_execute_with_course_filter(self, mock_vector_store, sample_search_results):
        """Test search with course name filter."""
        # Setup
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = sample_search_results

        # Execute
        result = tool.execute(
            query="supervised learning",
            course_name="Machine Learning"
        )

        # Verify
        mock_vector_store.search.assert_called_once_with(
            query="supervised learning",
            course_name="Machine Learning",
            lesson_number=None
        )
        assert isinstance(result, str)

    def test_execute_with_lesson_filter(self, mock_vector_store, sample_search_results):
        """Test search with lesson number filter."""
        # Setup
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = sample_search_results

        # Execute
        result = tool.execute(
            query="linear regression",
            lesson_number=1
        )

        # Verify
        mock_vector_store.search.assert_called_once_with(
            query="linear regression",
            course_name=None,
            lesson_number=1
        )
        assert isinstance(result, str)

    def test_execute_with_both_filters(self, mock_vector_store, sample_search_results):
        """Test search with both course and lesson filters."""
        # Setup
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = sample_search_results

        # Execute
        result = tool.execute(
            query="decision trees",
            course_name="ML Course",
            lesson_number=2
        )

        # Verify
        mock_vector_store.search.assert_called_once_with(
            query="decision trees",
            course_name="ML Course",
            lesson_number=2
        )
        assert isinstance(result, str)

    def test_execute_empty_results(self, mock_vector_store, empty_search_results):
        """Test handling of empty search results."""
        # Setup
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = empty_search_results

        # Execute
        result = tool.execute(query="nonexistent topic")

        # Verify
        assert "No relevant content found" in result

    def test_execute_empty_results_with_course_filter(self, mock_vector_store, empty_search_results):
        """Test empty results message includes course filter info."""
        # Setup
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = empty_search_results

        # Execute
        result = tool.execute(
            query="quantum physics",
            course_name="Machine Learning"
        )

        # Verify
        assert "No relevant content found" in result
        assert "Machine Learning" in result

    def test_execute_empty_results_with_lesson_filter(self, mock_vector_store, empty_search_results):
        """Test empty results message includes lesson filter info."""
        # Setup
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = empty_search_results

        # Execute
        result = tool.execute(
            query="advanced topics",
            lesson_number=5
        )

        # Verify
        assert "No relevant content found" in result
        assert "lesson 5" in result

    def test_execute_error_from_vector_store(self, mock_vector_store, error_search_results):
        """Test handling of error from vector store."""
        # Setup
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = error_search_results

        # Execute
        result = tool.execute(query="test query")

        # Verify
        assert "Search error" in result

    def test_source_tracking_with_links(self, mock_vector_store, sample_search_results):
        """Test that sources are tracked correctly with lesson links."""
        # Setup
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = sample_search_results
        mock_vector_store.get_lesson_link.side_effect = [
            "https://example.com/lesson-0",
            "https://example.com/lesson-1"
        ]

        # Execute
        result = tool.execute(query="machine learning")

        # Verify sources were tracked
        assert len(tool.last_sources) == 2

        # Verify source format
        assert_source_format(tool.last_sources)

        # Verify source content
        assert tool.last_sources[0]["text"] == "Introduction to Machine Learning - Lesson 0"
        assert tool.last_sources[0]["link"] == "https://example.com/lesson-0"

        assert tool.last_sources[1]["text"] == "Introduction to Machine Learning - Lesson 1"
        assert tool.last_sources[1]["link"] == "https://example.com/lesson-1"

    def test_source_tracking_without_lesson_number(self, mock_vector_store):
        """Test source tracking when lesson_number is None."""
        # Setup
        tool = CourseSearchTool(mock_vector_store)

        # Create results with None lesson_number
        results = SearchResults(
            documents=["Course introduction content"],
            metadata=[{
                "course_title": "Data Science Course",
                "lesson_number": None,
                "chunk_index": 0
            }],
            distances=[0.1],
            error=None
        )
        mock_vector_store.search.return_value = results

        # Execute
        result = tool.execute(query="introduction")

        # Verify sources
        assert len(tool.last_sources) == 1
        assert tool.last_sources[0]["text"] == "Data Science Course"
        assert tool.last_sources[0]["link"] is None

    def test_source_tracking_link_is_none(self, mock_vector_store, sample_search_results):
        """Test source tracking when get_lesson_link returns None."""
        # Setup
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = sample_search_results
        mock_vector_store.get_lesson_link.return_value = None  # No link available

        # Execute
        result = tool.execute(query="test")

        # Verify sources have None links
        assert tool.last_sources[0]["link"] is None
        assert tool.last_sources[1]["link"] is None

    def test_multiple_results_formatting(self, mock_vector_store):
        """Test that multiple results are formatted correctly."""
        # Setup
        tool = CourseSearchTool(mock_vector_store)

        results = create_search_results(
            documents=[
                "First document about neural networks",
                "Second document about deep learning",
                "Third document about CNNs"
            ],
            course_title="Deep Learning Course",
            lesson_numbers=[1, 1, 2]
        )
        mock_vector_store.search.return_value = results
        mock_vector_store.get_lesson_link.return_value = None

        # Execute
        result = tool.execute(query="neural networks")

        # Verify formatting
        assert "[Deep Learning Course - Lesson 1]" in result
        assert "[Deep Learning Course - Lesson 2]" in result
        assert "First document" in result
        assert "Second document" in result
        assert "Third document" in result

        # Verify results are separated by double newlines
        assert "\n\n" in result

    def test_result_header_format_with_lesson(self, mock_vector_store):
        """Test result header format when lesson number is present."""
        # Setup
        tool = CourseSearchTool(mock_vector_store)

        results = create_search_results(
            documents=["Test content"],
            course_title="Test Course",
            lesson_numbers=[3]
        )
        mock_vector_store.search.return_value = results
        mock_vector_store.get_lesson_link.return_value = None

        # Execute
        result = tool.execute(query="test")

        # Verify header format
        assert "[Test Course - Lesson 3]" in result

    def test_result_header_format_without_lesson(self, mock_vector_store):
        """Test result header format when lesson number is None."""
        # Setup
        tool = CourseSearchTool(mock_vector_store)

        results = SearchResults(
            documents=["Test content"],
            metadata=[{
                "course_title": "Test Course",
                "lesson_number": None,
                "chunk_index": 0
            }],
            distances=[0.1],
            error=None
        )
        mock_vector_store.search.return_value = results

        # Execute
        result = tool.execute(query="test")

        # Verify header format (no lesson number)
        assert "[Test Course]" in result
        assert "Lesson" not in result

    def test_get_lesson_link_called_correctly(self, mock_vector_store, sample_search_results):
        """Test that get_lesson_link is called with correct parameters."""
        # Setup
        tool = CourseSearchTool(mock_vector_store)
        mock_vector_store.search.return_value = sample_search_results
        mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson"

        # Execute
        result = tool.execute(query="test")

        # Verify get_lesson_link calls
        assert mock_vector_store.get_lesson_link.call_count == 2
        mock_vector_store.get_lesson_link.assert_any_call(
            "Introduction to Machine Learning",
            0
        )
        mock_vector_store.get_lesson_link.assert_any_call(
            "Introduction to Machine Learning",
            1
        )
