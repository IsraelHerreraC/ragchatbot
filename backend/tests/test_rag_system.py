"""
Tests for RAGSystem query handling and integration.

This test suite verifies:
- End-to-end query processing
- Session management integration
- Source retrieval and tracking
- Tool manager integration
- Conversation history handling
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from config import Config
from rag_system import RAGSystem


class TestRAGSystemQueryProcessing:
    """Tests for RAGSystem.query() method."""

    @patch("rag_system.SessionManager")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.VectorStore")
    @patch("rag_system.DocumentProcessor")
    @patch("rag_system.ToolManager")
    def test_query_without_session_id(
        self,
        mock_tool_manager_class,
        mock_doc_processor_class,
        mock_vector_store_class,
        mock_ai_generator_class,
        mock_session_manager_class,
    ):
        """Test query processing without session ID."""
        # Setup mocks
        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "Test response"
        mock_ai_generator_class.return_value = mock_ai_gen

        mock_session_mgr = Mock()
        mock_session_mgr.get_conversation_history.return_value = None
        mock_session_manager_class.return_value = mock_session_mgr

        mock_tool_mgr = Mock()
        mock_tool_mgr.get_last_sources.return_value = []
        mock_tool_manager_class.return_value = mock_tool_mgr

        # Create RAG system
        config = Config()
        rag_system = RAGSystem(config)
        rag_system.tool_manager = mock_tool_mgr

        # Execute
        response, sources = rag_system.query("What is ML?", session_id=None)

        # Verify
        assert response == "Test response"
        assert sources == []
        mock_ai_gen.generate_response.assert_called_once()

    @patch("rag_system.SessionManager")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.VectorStore")
    @patch("rag_system.DocumentProcessor")
    @patch("rag_system.ToolManager")
    def test_query_with_existing_session(
        self,
        mock_tool_manager_class,
        mock_doc_processor_class,
        mock_vector_store_class,
        mock_ai_generator_class,
        mock_session_manager_class,
    ):
        """Test query with existing session retrieves history."""
        # Setup mocks
        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "Response with context"
        mock_ai_generator_class.return_value = mock_ai_gen

        conversation_history = "User: Hello\nAssistant: Hi!"
        mock_session_mgr = Mock()
        mock_session_mgr.get_conversation_history.return_value = conversation_history
        mock_session_manager_class.return_value = mock_session_mgr

        mock_tool_mgr = Mock()
        mock_tool_mgr.get_last_sources.return_value = []
        mock_tool_manager_class.return_value = mock_tool_mgr

        # Create RAG system
        config = Config()
        rag_system = RAGSystem(config)
        rag_system.tool_manager = mock_tool_mgr

        # Execute
        response, sources = rag_system.query("What is AI?", session_id="session_1")

        # Verify
        assert response == "Response with context"
        mock_session_mgr.get_conversation_history.assert_called_once_with("session_1")

        # Verify history was passed to AI generator
        call_args = mock_ai_gen.generate_response.call_args
        assert call_args.kwargs["conversation_history"] == conversation_history

    @patch("rag_system.SessionManager")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.VectorStore")
    @patch("rag_system.DocumentProcessor")
    @patch("rag_system.ToolManager")
    def test_session_history_updated_after_query(
        self,
        mock_tool_manager_class,
        mock_doc_processor_class,
        mock_vector_store_class,
        mock_ai_generator_class,
        mock_session_manager_class,
    ):
        """Test that conversation history is updated after query."""
        # Setup mocks
        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "AI response"
        mock_ai_generator_class.return_value = mock_ai_gen

        mock_session_mgr = Mock()
        mock_session_mgr.get_conversation_history.return_value = None
        mock_session_manager_class.return_value = mock_session_mgr

        mock_tool_mgr = Mock()
        mock_tool_mgr.get_last_sources.return_value = []
        mock_tool_manager_class.return_value = mock_tool_mgr

        # Create RAG system
        config = Config()
        rag_system = RAGSystem(config)
        rag_system.tool_manager = mock_tool_mgr

        # Execute
        query_text = "Tell me about ML"
        response, sources = rag_system.query(query_text, session_id="session_1")

        # Verify history was updated
        mock_session_mgr.add_exchange.assert_called_once_with(
            "session_1", query_text, "AI response"
        )


class TestRAGSystemSourceHandling:
    """Tests for source retrieval and tracking."""

    @patch("rag_system.SessionManager")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.VectorStore")
    @patch("rag_system.DocumentProcessor")
    @patch("rag_system.ToolManager")
    def test_sources_retrieved_from_tool_manager(
        self,
        mock_tool_manager_class,
        mock_doc_processor_class,
        mock_vector_store_class,
        mock_ai_generator_class,
        mock_session_manager_class,
    ):
        """Test that sources are retrieved from tool manager."""
        # Setup mocks
        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "Response"
        mock_ai_generator_class.return_value = mock_ai_gen

        mock_session_mgr = Mock()
        mock_session_mgr.get_conversation_history.return_value = None
        mock_session_manager_class.return_value = mock_session_mgr

        test_sources = [
            {"text": "ML Course - Lesson 1", "link": "https://example.com/lesson-1"},
            {"text": "ML Course - Lesson 2", "link": "https://example.com/lesson-2"},
        ]
        mock_tool_mgr = Mock()
        mock_tool_mgr.get_last_sources.return_value = test_sources
        mock_tool_manager_class.return_value = mock_tool_mgr

        # Create RAG system
        config = Config()
        rag_system = RAGSystem(config)
        rag_system.tool_manager = mock_tool_mgr

        # Execute
        response, sources = rag_system.query("Test query", session_id="session_1")

        # Verify
        assert sources == test_sources
        mock_tool_mgr.get_last_sources.assert_called_once()

    @patch("rag_system.SessionManager")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.VectorStore")
    @patch("rag_system.DocumentProcessor")
    @patch("rag_system.ToolManager")
    def test_sources_reset_after_retrieval(
        self,
        mock_tool_manager_class,
        mock_doc_processor_class,
        mock_vector_store_class,
        mock_ai_generator_class,
        mock_session_manager_class,
    ):
        """Test that sources are reset after being retrieved."""
        # Setup mocks
        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "Response"
        mock_ai_generator_class.return_value = mock_ai_gen

        mock_session_mgr = Mock()
        mock_session_manager_class.return_value = mock_session_mgr

        mock_tool_mgr = Mock()
        mock_tool_mgr.get_last_sources.return_value = [{"text": "Source", "link": None}]
        mock_tool_manager_class.return_value = mock_tool_mgr

        # Create RAG system
        config = Config()
        rag_system = RAGSystem(config)
        rag_system.tool_manager = mock_tool_mgr

        # Execute
        response, sources = rag_system.query("Test", session_id="session_1")

        # Verify sources were reset
        mock_tool_mgr.reset_sources.assert_called_once()

    @patch("rag_system.SessionManager")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.VectorStore")
    @patch("rag_system.DocumentProcessor")
    @patch("rag_system.ToolManager")
    def test_empty_sources_when_no_tool_called(
        self,
        mock_tool_manager_class,
        mock_doc_processor_class,
        mock_vector_store_class,
        mock_ai_generator_class,
        mock_session_manager_class,
    ):
        """Test that empty sources are returned when no tool is called."""
        # Setup mocks
        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "General knowledge answer"
        mock_ai_generator_class.return_value = mock_ai_gen

        mock_session_mgr = Mock()
        mock_session_manager_class.return_value = mock_session_mgr

        mock_tool_mgr = Mock()
        mock_tool_mgr.get_last_sources.return_value = []  # No sources
        mock_tool_manager_class.return_value = mock_tool_mgr

        # Create RAG system
        config = Config()
        rag_system = RAGSystem(config)
        rag_system.tool_manager = mock_tool_mgr

        # Execute - general question that doesn't need tools
        response, sources = rag_system.query("What is 2+2?", session_id="session_1")

        # Verify
        assert sources == []


class TestRAGSystemToolIntegration:
    """Tests for tool manager integration."""

    @patch("rag_system.SessionManager")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.VectorStore")
    @patch("rag_system.DocumentProcessor")
    @patch("rag_system.ToolManager")
    def test_tool_definitions_passed_to_ai_generator(
        self,
        mock_tool_manager_class,
        mock_doc_processor_class,
        mock_vector_store_class,
        mock_ai_generator_class,
        mock_session_manager_class,
    ):
        """Test that tool definitions are passed to AI generator."""
        # Setup mocks
        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "Response"
        mock_ai_generator_class.return_value = mock_ai_gen

        mock_session_mgr = Mock()
        mock_session_manager_class.return_value = mock_session_mgr

        tool_definitions = [
            {"name": "search_course_content", "description": "Search courses"},
            {"name": "get_course_outline", "description": "Get outline"},
        ]
        mock_tool_mgr = Mock()
        mock_tool_mgr.get_tool_definitions.return_value = tool_definitions
        mock_tool_mgr.get_last_sources.return_value = []
        mock_tool_manager_class.return_value = mock_tool_mgr

        # Create RAG system
        config = Config()
        rag_system = RAGSystem(config)
        rag_system.tool_manager = mock_tool_mgr

        # Execute
        response, sources = rag_system.query("Test query", session_id="session_1")

        # Verify tool definitions were passed
        call_args = mock_ai_gen.generate_response.call_args
        assert call_args.kwargs["tools"] == tool_definitions

    @patch("rag_system.SessionManager")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.VectorStore")
    @patch("rag_system.DocumentProcessor")
    @patch("rag_system.ToolManager")
    def test_tool_manager_passed_to_ai_generator(
        self,
        mock_tool_manager_class,
        mock_doc_processor_class,
        mock_vector_store_class,
        mock_ai_generator_class,
        mock_session_manager_class,
    ):
        """Test that tool manager instance is passed to AI generator."""
        # Setup mocks
        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = "Response"
        mock_ai_generator_class.return_value = mock_ai_gen

        mock_session_mgr = Mock()
        mock_session_manager_class.return_value = mock_session_mgr

        mock_tool_mgr = Mock()
        mock_tool_mgr.get_tool_definitions.return_value = []
        mock_tool_mgr.get_last_sources.return_value = []
        mock_tool_manager_class.return_value = mock_tool_mgr

        # Create RAG system
        config = Config()
        rag_system = RAGSystem(config)
        rag_system.tool_manager = mock_tool_mgr

        # Execute
        response, sources = rag_system.query("Test", session_id="session_1")

        # Verify tool manager was passed
        call_args = mock_ai_gen.generate_response.call_args
        assert call_args.kwargs["tool_manager"] == mock_tool_mgr


class TestRAGSystemEndToEnd:
    """End-to-end integration tests."""

    @patch("rag_system.SessionManager")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.VectorStore")
    @patch("rag_system.DocumentProcessor")
    @patch("rag_system.ToolManager")
    def test_full_query_flow_with_tool_call(
        self,
        mock_tool_manager_class,
        mock_doc_processor_class,
        mock_vector_store_class,
        mock_ai_generator_class,
        mock_session_manager_class,
    ):
        """Test complete query flow when tool is called."""
        # Setup mocks
        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = (
            "ML is a subset of AI that focuses on learning from data."
        )
        mock_ai_generator_class.return_value = mock_ai_gen

        mock_session_mgr = Mock()
        mock_session_mgr.get_conversation_history.return_value = None
        mock_session_manager_class.return_value = mock_session_mgr

        sources_from_tool = [
            {"text": "ML Course - Lesson 1", "link": "https://example.com/lesson-1"}
        ]
        mock_tool_mgr = Mock()
        mock_tool_mgr.get_tool_definitions.return_value = [
            {"name": "search_course_content"}
        ]
        mock_tool_mgr.get_last_sources.return_value = sources_from_tool
        mock_tool_manager_class.return_value = mock_tool_mgr

        # Create RAG system
        config = Config()
        rag_system = RAGSystem(config)
        rag_system.tool_manager = mock_tool_mgr

        # Execute
        query_text = "What is machine learning?"
        response, sources = rag_system.query(query_text, session_id="session_1")

        # Verify complete flow
        assert response == "ML is a subset of AI that focuses on learning from data."
        assert sources == sources_from_tool

        # Verify AI generator was called correctly
        mock_ai_gen.generate_response.assert_called_once()
        call_args = mock_ai_gen.generate_response.call_args
        assert "Answer this question" in call_args.kwargs["query"]
        assert query_text in call_args.kwargs["query"]

        # Verify session was updated with original query (not formatted prompt)
        mock_session_mgr.add_exchange.assert_called_once_with(
            "session_1", query_text, response
        )

        # Verify sources were retrieved and reset
        mock_tool_mgr.get_last_sources.assert_called_once()
        mock_tool_mgr.reset_sources.assert_called_once()

    @patch("rag_system.SessionManager")
    @patch("rag_system.AIGenerator")
    @patch("rag_system.VectorStore")
    @patch("rag_system.DocumentProcessor")
    @patch("rag_system.ToolManager")
    def test_query_with_conversation_context(
        self,
        mock_tool_manager_class,
        mock_doc_processor_class,
        mock_vector_store_class,
        mock_ai_generator_class,
        mock_session_manager_class,
    ):
        """Test query with existing conversation context."""
        # Setup mocks
        mock_ai_gen = Mock()
        mock_ai_gen.generate_response.return_value = (
            "Yes, supervised learning uses labeled data."
        )
        mock_ai_generator_class.return_value = mock_ai_gen

        history = "User: What is machine learning?\nAssistant: ML is a subset of AI."
        mock_session_mgr = Mock()
        mock_session_mgr.get_conversation_history.return_value = history
        mock_session_manager_class.return_value = mock_session_mgr

        mock_tool_mgr = Mock()
        mock_tool_mgr.get_tool_definitions.return_value = []
        mock_tool_mgr.get_last_sources.return_value = []
        mock_tool_manager_class.return_value = mock_tool_mgr

        # Create RAG system
        config = Config()
        rag_system = RAGSystem(config)
        rag_system.tool_manager = mock_tool_mgr

        # Execute
        response, sources = rag_system.query(
            "What about supervised learning?", session_id="session_1"
        )

        # Verify history was retrieved and passed
        mock_session_mgr.get_conversation_history.assert_called_once_with("session_1")
        call_args = mock_ai_gen.generate_response.call_args
        assert call_args.kwargs["conversation_history"] == history
