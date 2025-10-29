"""
Helper functions and utilities for testing the RAG system.
"""

from typing import Any, Dict, List, Optional
from unittest.mock import Mock

from models import Course, CourseChunk, Lesson
from vector_store import SearchResults


def create_search_results(
    documents: List[str],
    course_title: str = "Test Course",
    lesson_numbers: Optional[List[int]] = None,
    error: Optional[str] = None,
) -> SearchResults:
    """
    Create SearchResults object with given parameters.

    Args:
        documents: List of document texts
        course_title: Course title for metadata
        lesson_numbers: List of lesson numbers (defaults to sequential 0, 1, 2...)
        error: Optional error message

    Returns:
        SearchResults object
    """
    if lesson_numbers is None:
        lesson_numbers = list(range(len(documents)))

    metadata = [
        {"course_title": course_title, "lesson_number": lesson_num, "chunk_index": i}
        for i, lesson_num in enumerate(lesson_numbers)
    ]

    distances = [0.1 * (i + 1) for i in range(len(documents))]

    return SearchResults(
        documents=documents, metadata=metadata, distances=distances, error=error
    )


def create_course(
    title: str = "Test Course",
    num_lessons: int = 3,
    instructor: str = "Test Instructor",
    course_link: str = "https://example.com/course",
) -> Course:
    """
    Create a Course object with specified parameters.

    Args:
        title: Course title
        num_lessons: Number of lessons to create
        instructor: Instructor name
        course_link: Course URL

    Returns:
        Course object
    """
    lessons = [
        Lesson(
            lesson_number=i,
            title=f"Lesson {i}",
            lesson_link=f"{course_link}/lesson-{i}",
        )
        for i in range(num_lessons)
    ]

    return Course(
        title=title, course_link=course_link, instructor=instructor, lessons=lessons
    )


def create_anthropic_response(
    text: Optional[str] = None,
    tool_use: Optional[Dict[str, Any]] = None,
    stop_reason: str = "end_turn",
) -> Mock:
    """
    Create a mock Anthropic API response.

    Args:
        text: Text response content
        tool_use: Tool use dict with 'name' and 'input' keys
        stop_reason: Response stop reason

    Returns:
        Mock response object
    """
    mock_response = Mock()
    mock_response.stop_reason = stop_reason

    if text:
        content_block = Mock()
        content_block.type = "text"
        content_block.text = text
        mock_response.content = [content_block]
    elif tool_use:
        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.id = "tool_call_123"
        tool_block.name = tool_use.get("name", "search_course_content")
        tool_block.input = tool_use.get("input", {})
        mock_response.content = [tool_block]
    else:
        mock_response.content = []

    return mock_response


def assert_source_format(sources: List[Dict[str, Any]]):
    """
    Assert that sources are in the correct format.

    Args:
        sources: List of source dictionaries

    Raises:
        AssertionError: If format is incorrect
    """
    assert isinstance(sources, list), "Sources should be a list"

    for source in sources:
        assert isinstance(source, dict), f"Source should be dict, got {type(source)}"
        assert "text" in source, "Source should have 'text' key"
        assert isinstance(source["text"], str), "'text' should be a string"

        if "link" in source:
            assert isinstance(
                source["link"], (str, type(None))
            ), "'link' should be a string or None"


def create_mock_chroma_results(
    documents: List[str], metadatas: List[Dict[str, Any]], distances: List[float]
) -> Dict[str, List]:
    """
    Create mock ChromaDB query results structure.

    Args:
        documents: List of document texts
        metadatas: List of metadata dicts
        distances: List of distance scores

    Returns:
        Dict matching ChromaDB result structure
    """
    return {
        "documents": [documents],  # ChromaDB wraps in another list
        "metadatas": [metadatas],
        "distances": [distances],
        "ids": [[f"doc_{i}" for i in range(len(documents))]],
    }
