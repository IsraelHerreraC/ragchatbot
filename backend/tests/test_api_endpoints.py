"""
API endpoint tests for the RAG system FastAPI application.

These tests verify the behavior of all API endpoints including:
- POST /api/query - Query processing
- GET /api/courses - Course statistics
- POST /api/session/clear - Session management
- GET / - Root endpoint
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException


# Mark all tests in this module as API tests
pytestmark = pytest.mark.api


class TestQueryEndpoint:
    """Test suite for POST /api/query endpoint"""

    @pytest.mark.asyncio
    async def test_query_without_session_id(self, async_client, mock_rag_system):
        """Test querying without providing a session ID - should create new session"""
        response = await async_client.post(
            "/api/query",
            json={"query": "What is machine learning?"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data

        # Verify session was created
        assert data["session_id"] == "session_1"
        mock_rag_system.session_manager.create_session.assert_called_once()

        # Verify RAG system was queried
        mock_rag_system.query.assert_called_once_with(
            "What is machine learning?",
            "session_1"
        )

    @pytest.mark.asyncio
    async def test_query_with_existing_session_id(self, async_client, mock_rag_system):
        """Test querying with an existing session ID"""
        response = await async_client.post(
            "/api/query",
            json={
                "query": "Tell me about neural networks",
                "session_id": "session_123"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify session ID is preserved
        assert data["session_id"] == "session_123"

        # Verify session was NOT created (already exists)
        mock_rag_system.session_manager.create_session.assert_not_called()

        # Verify RAG system was queried with correct session
        mock_rag_system.query.assert_called_once_with(
            "Tell me about neural networks",
            "session_123"
        )

    @pytest.mark.asyncio
    async def test_query_response_format(self, async_client, mock_rag_system):
        """Test that query response has correct format with answer and sources"""
        response = await async_client.post(
            "/api/query",
            json={"query": "Explain supervised learning"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify answer
        assert data["answer"] == "Machine learning is a subset of artificial intelligence."

        # Verify sources format
        assert len(data["sources"]) == 2
        assert data["sources"][0]["text"] == "Introduction to Machine Learning - Lesson 0"
        assert data["sources"][0]["link"] == "https://example.com/ml-course/lesson-0"
        assert data["sources"][1]["text"] == "Introduction to Machine Learning - Lesson 1"
        assert data["sources"][1]["link"] == "https://example.com/ml-course/lesson-1"

    @pytest.mark.asyncio
    async def test_query_empty_string(self, async_client, mock_rag_system):
        """Test querying with empty string"""
        response = await async_client.post(
            "/api/query",
            json={"query": ""}
        )

        # Should still succeed - validation happens in RAG system
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_query_missing_query_field(self, async_client):
        """Test request without required 'query' field"""
        response = await async_client.post(
            "/api/query",
            json={"session_id": "session_1"}
        )

        # Should return 422 Unprocessable Entity (Pydantic validation error)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_query_invalid_json(self, async_client):
        """Test request with invalid JSON"""
        response = await async_client.post(
            "/api/query",
            content="invalid json{",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_query_rag_system_error(self, async_client, mock_rag_system):
        """Test handling of RAG system errors"""
        # Make the RAG system raise an exception
        mock_rag_system.query.side_effect = Exception("Database connection failed")

        response = await async_client.post(
            "/api/query",
            json={"query": "What is AI?"}
        )

        # Should return 500 Internal Server Error
        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]


class TestCoursesEndpoint:
    """Test suite for GET /api/courses endpoint"""

    @pytest.mark.asyncio
    async def test_get_courses_success(self, async_client, mock_rag_system):
        """Test successful retrieval of course statistics"""
        response = await async_client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "total_courses" in data
        assert "course_titles" in data

        # Verify data values
        assert data["total_courses"] == 2
        assert len(data["course_titles"]) == 2
        assert "Introduction to Machine Learning" in data["course_titles"]
        assert "Deep Learning Fundamentals" in data["course_titles"]

        # Verify RAG system method was called
        mock_rag_system.get_course_analytics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_courses_empty_database(self, async_client, mock_rag_system):
        """Test course statistics with no courses in database"""
        # Mock empty course list
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": []
        }

        response = await async_client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()

        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    @pytest.mark.asyncio
    async def test_get_courses_analytics_error(self, async_client, mock_rag_system):
        """Test handling of errors when retrieving course analytics"""
        # Make get_course_analytics raise an exception
        mock_rag_system.get_course_analytics.side_effect = Exception("ChromaDB connection error")

        response = await async_client.get("/api/courses")

        # Should return 500 Internal Server Error
        assert response.status_code == 500
        assert "ChromaDB connection error" in response.json()["detail"]


class TestClearSessionEndpoint:
    """Test suite for POST /api/session/clear endpoint"""

    @pytest.mark.asyncio
    async def test_clear_session_success(self, async_client, mock_rag_system):
        """Test successful session clearing"""
        response = await async_client.post(
            "/api/session/clear",
            json={"session_id": "session_123"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        assert "session_123" in data["message"]
        assert "cleared successfully" in data["message"]

        # Verify session manager was called
        mock_rag_system.session_manager.clear_session.assert_called_once_with("session_123")

    @pytest.mark.asyncio
    async def test_clear_session_missing_session_id(self, async_client):
        """Test clearing session without providing session_id"""
        response = await async_client.post(
            "/api/session/clear",
            json={}
        )

        # Should return 422 Unprocessable Entity (Pydantic validation error)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_clear_session_error(self, async_client, mock_rag_system):
        """Test handling of errors when clearing session"""
        # Make clear_session raise an exception
        mock_rag_system.session_manager.clear_session.side_effect = Exception("Session not found")

        response = await async_client.post(
            "/api/session/clear",
            json={"session_id": "nonexistent_session"}
        )

        # Should return 500 Internal Server Error
        assert response.status_code == 500
        assert "Session not found" in response.json()["detail"]


class TestRootEndpoint:
    """Test suite for GET / (root) endpoint"""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, async_client):
        """Test root endpoint returns welcome message"""
        response = await async_client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "Course Materials RAG System API" in data["message"]


class TestCORSConfiguration:
    """Test suite for CORS middleware configuration"""

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, async_client):
        """Test that CORS headers are present in responses"""
        response = await async_client.options(
            "/api/query",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            }
        )

        # CORS preflight should succeed
        assert response.status_code == 200

        # Verify CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers


class TestEndpointIntegration:
    """Integration tests across multiple endpoints"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_query_and_session_workflow(self, async_client, mock_rag_system):
        """Test complete workflow: query -> get courses -> clear session"""
        # Step 1: Make a query (creates session)
        query_response = await async_client.post(
            "/api/query",
            json={"query": "What is deep learning?"}
        )
        assert query_response.status_code == 200
        session_id = query_response.json()["session_id"]

        # Step 2: Get course statistics
        courses_response = await async_client.get("/api/courses")
        assert courses_response.status_code == 200
        assert courses_response.json()["total_courses"] > 0

        # Step 3: Clear the session
        clear_response = await async_client.post(
            "/api/session/clear",
            json={"session_id": session_id}
        )
        assert clear_response.status_code == 200
        assert clear_response.json()["success"] is True

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_queries_same_session(self, async_client, mock_rag_system):
        """Test multiple queries using the same session ID"""
        session_id = "test_session_456"

        # First query
        response1 = await async_client.post(
            "/api/query",
            json={"query": "What is AI?", "session_id": session_id}
        )
        assert response1.status_code == 200
        assert response1.json()["session_id"] == session_id

        # Second query with same session
        response2 = await async_client.post(
            "/api/query",
            json={"query": "Tell me more", "session_id": session_id}
        )
        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id

        # Verify both queries were processed
        assert mock_rag_system.query.call_count == 2
