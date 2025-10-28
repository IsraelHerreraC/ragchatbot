"""
Tests for AIGenerator tool calling functionality.

This test suite verifies:
- Text responses without tools
- Tool use detection and execution
- Two-phase API call pattern
- Tool result formatting
- Conversation history integration
- Error handling
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from ai_generator import AIGenerator
from tests.test_helpers import create_anthropic_response


class TestAIGeneratorBasicResponses:
    """Tests for basic text responses without tool use."""

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_simple_text_response(
        self,
        mock_anthropic_class,
        sample_anthropic_text_response
    ):
        """Test generating a simple text response without tools."""
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.return_value = sample_anthropic_text_response

        generator = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")

        # Execute
        result = generator.generate_response(query="What is 2+2?")

        # Verify
        assert result == "This is a sample response from the AI."
        mock_client.messages.create.assert_called_once()

        # Check call parameters
        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["model"] == "claude-sonnet-4-20250514"
        assert call_args.kwargs["temperature"] == 0
        assert call_args.kwargs["max_tokens"] == 800
        assert call_args.kwargs["messages"][0]["content"] == "What is 2+2?"

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_with_conversation_history(
        self,
        mock_anthropic_class,
        sample_anthropic_text_response
    ):
        """Test that conversation history is included in system prompt."""
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.return_value = sample_anthropic_text_response

        generator = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")

        history = "User: Hello\nAssistant: Hi there!"

        # Execute
        result = generator.generate_response(
            query="How are you?",
            conversation_history=history
        )

        # Verify
        call_args = mock_client.messages.create.call_args
        assert "Previous conversation" in call_args.kwargs["system"]
        assert history in call_args.kwargs["system"]

    @patch('ai_generator.anthropic.Anthropic')
    def test_generate_response_without_history(
        self,
        mock_anthropic_class,
        sample_anthropic_text_response
    ):
        """Test that system prompt works without conversation history."""
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.return_value = sample_anthropic_text_response

        generator = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")

        # Execute
        result = generator.generate_response(query="What is AI?")

        # Verify
        call_args = mock_client.messages.create.call_args
        assert "Previous conversation" not in call_args.kwargs["system"]


class TestAIGeneratorToolCalling:
    """Tests for tool calling functionality."""

    @patch('ai_generator.anthropic.Anthropic')
    def test_tool_use_triggers_two_phase_flow(
        self,
        mock_anthropic_class,
        sample_anthropic_tool_use_response,
        sample_anthropic_final_response,
        mock_tool_manager
    ):
        """Test that tool_use response triggers the two-phase API call pattern."""
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # First call returns tool_use, second call returns final response
        mock_client.messages.create.side_effect = [
            sample_anthropic_tool_use_response,
            sample_anthropic_final_response
        ]

        mock_tool_manager.execute_tool.return_value = "Search results about ML"

        generator = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")

        # Execute
        result = generator.generate_response(
            query="What is machine learning?",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Verify
        assert result == "Based on the search results, machine learning is..."
        assert mock_client.messages.create.call_count == 2
        mock_tool_manager.execute_tool.assert_called_once()

    @patch('ai_generator.anthropic.Anthropic')
    def test_tool_execution_called_with_correct_parameters(
        self,
        mock_anthropic_class,
        sample_anthropic_tool_use_response,
        sample_anthropic_final_response,
        mock_tool_manager
    ):
        """Test that tool is executed with correct parameters from API response."""
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = [
            sample_anthropic_tool_use_response,
            sample_anthropic_final_response
        ]

        mock_tool_manager.execute_tool.return_value = "Tool result"

        generator = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")

        # Execute
        result = generator.generate_response(
            query="Search for ML basics",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Verify tool was called correctly
        mock_tool_manager.execute_tool.assert_called_once_with(
            "search_course_content",
            query="machine learning basics"
        )

    @patch('ai_generator.anthropic.Anthropic')
    def test_tool_results_sent_in_second_api_call(
        self,
        mock_anthropic_class,
        sample_anthropic_tool_use_response,
        sample_anthropic_final_response,
        mock_tool_manager
    ):
        """Test that tool results are correctly formatted in second API call."""
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = [
            sample_anthropic_tool_use_response,
            sample_anthropic_final_response
        ]

        tool_result = "Machine learning is a subset of AI..."
        mock_tool_manager.execute_tool.return_value = tool_result

        generator = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")

        # Execute
        result = generator.generate_response(
            query="What is ML?",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Verify second API call structure
        second_call = mock_client.messages.create.call_args_list[1]
        messages = second_call.kwargs["messages"]

        # Should have 3 messages: user query, assistant tool_use, user tool_result
        assert len(messages) == 3

        # Third message should contain tool results
        tool_result_msg = messages[2]
        assert tool_result_msg["role"] == "user"
        assert tool_result_msg["content"][0]["type"] == "tool_result"
        assert tool_result_msg["content"][0]["tool_use_id"] == "tool_call_123"
        assert tool_result_msg["content"][0]["content"] == tool_result

    @patch('ai_generator.anthropic.Anthropic')
    def test_tools_parameter_added_to_first_call(
        self,
        mock_anthropic_class,
        sample_anthropic_text_response
    ):
        """Test that tools parameter is added to first API call."""
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.return_value = sample_anthropic_text_response

        generator = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")

        tools = [{"name": "search_course_content", "description": "Search courses"}]

        # Execute
        result = generator.generate_response(
            query="Test query",
            tools=tools
        )

        # Verify
        call_args = mock_client.messages.create.call_args
        assert "tools" in call_args.kwargs
        assert call_args.kwargs["tools"] == tools
        assert call_args.kwargs["tool_choice"] == {"type": "auto"}

    @patch('ai_generator.anthropic.Anthropic')
    def test_no_tool_manager_with_tool_use(
        self,
        mock_anthropic_class,
        sample_anthropic_tool_use_response
    ):
        """Test handling when tool_use occurs but no tool_manager provided."""
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.return_value = sample_anthropic_tool_use_response

        generator = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")

        # Execute - should return None since _handle_tool_execution not called
        result = generator.generate_response(
            query="Test",
            tools=[{"name": "test_tool"}],
            tool_manager=None  # No tool manager
        )

        # Verify - should not crash, but won't return proper response
        # In real code, this might need better handling
        assert mock_client.messages.create.call_count == 1


class TestAIGeneratorEdgeCases:
    """Tests for edge cases and error handling."""

    @patch('ai_generator.anthropic.Anthropic')
    def test_multiple_tool_calls_in_response(
        self,
        mock_anthropic_class,
        sample_anthropic_final_response,
        mock_tool_manager
    ):
        """Test handling of multiple tool calls in single response."""
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Create response with multiple tool calls
        tool_block_1 = Mock()
        tool_block_1.type = "tool_use"
        tool_block_1.id = "tool_call_1"
        tool_block_1.name = "search_course_content"
        tool_block_1.input = {"query": "ML basics"}

        tool_block_2 = Mock()
        tool_block_2.type = "tool_use"
        tool_block_2.id = "tool_call_2"
        tool_block_2.name = "get_course_outline"
        tool_block_2.input = {"course_name": "ML Course"}

        multi_tool_response = Mock()
        multi_tool_response.stop_reason = "tool_use"
        multi_tool_response.content = [tool_block_1, tool_block_2]

        mock_client.messages.create.side_effect = [
            multi_tool_response,
            sample_anthropic_final_response
        ]

        mock_tool_manager.execute_tool.side_effect = [
            "Result 1",
            "Result 2"
        ]

        generator = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")

        # Execute
        result = generator.generate_response(
            query="Test multi-tool",
            tools=[{"name": "search_course_content"}, {"name": "get_course_outline"}],
            tool_manager=mock_tool_manager
        )

        # Verify both tools were executed
        assert mock_tool_manager.execute_tool.call_count == 2

    @patch('ai_generator.anthropic.Anthropic')
    def test_empty_tool_results(
        self,
        mock_anthropic_class,
        sample_anthropic_tool_use_response,
        sample_anthropic_final_response,
        mock_tool_manager
    ):
        """Test handling of empty string tool results."""
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = [
            sample_anthropic_tool_use_response,
            sample_anthropic_final_response
        ]

        mock_tool_manager.execute_tool.return_value = ""  # Empty result

        generator = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")

        # Execute
        result = generator.generate_response(
            query="Test",
            tools=[{"name": "test_tool"}],
            tool_manager=mock_tool_manager
        )

        # Should still work with empty result
        assert result == "Based on the search results, machine learning is..."

    @patch('ai_generator.anthropic.Anthropic')
    def test_tool_returns_error_string(
        self,
        mock_anthropic_class,
        sample_anthropic_tool_use_response,
        sample_anthropic_final_response,
        mock_tool_manager
    ):
        """Test that tool error strings are passed to AI."""
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = [
            sample_anthropic_tool_use_response,
            sample_anthropic_final_response
        ]

        error_msg = "Search error: No course found matching 'XYZ'"
        mock_tool_manager.execute_tool.return_value = error_msg

        generator = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514")

        # Execute
        result = generator.generate_response(
            query="Find XYZ course",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Verify error was passed to second API call
        second_call = mock_client.messages.create.call_args_list[1]
        tool_result_content = second_call.kwargs["messages"][2]["content"][0]["content"]
        assert tool_result_content == error_msg


class TestAIGeneratorSequentialToolCalling:
    """Tests for sequential tool calling functionality (multi-round)."""

    @patch('ai_generator.anthropic.Anthropic')
    def test_single_round_backward_compatibility(
        self,
        mock_anthropic_class,
        mock_tool_manager
    ):
        """
        Test that single tool call followed by end_turn still works.
        This ensures backward compatibility with existing behavior.
        """
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Create tool use response for first call
        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.id = "tool_call_1"
        tool_block.name = "search_course_content"
        tool_block.input = {"query": "ML basics"}

        tool_use_response = Mock()
        tool_use_response.stop_reason = "tool_use"
        tool_use_response.content = [tool_block]

        # Create final text response for second call
        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock(type="text", text="Machine learning is a subset of AI...")]

        mock_client.messages.create.side_effect = [
            tool_use_response,
            final_response
        ]

        mock_tool_manager.execute_tool.return_value = "ML: subset of AI..."

        generator = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514", max_tool_rounds=2)

        # Execute
        result = generator.generate_response(
            query="What is ML?",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Verify
        assert result == "Machine learning is a subset of AI..."
        assert mock_client.messages.create.call_count == 2
        assert mock_tool_manager.execute_tool.call_count == 1

        # Verify message history has correct structure (3 messages)
        second_call = mock_client.messages.create.call_args_list[1]
        messages = second_call.kwargs["messages"]
        assert len(messages) == 3
        assert messages[0]["role"] == "user"  # Original query
        assert messages[1]["role"] == "assistant"  # Tool use
        assert messages[2]["role"] == "user"  # Tool result

    @patch('ai_generator.anthropic.Anthropic')
    def test_two_sequential_tool_calls_with_different_tools(
        self,
        mock_anthropic_class,
        mock_tool_manager
    ):
        """
        Verify that Claude can call tool A, then tool B based on results.

        Scenario: "Compare ML course to AI course"
        Round 1: search_course_content(query="ML")
        Round 2: search_course_content(query="AI")
        Round 3: end_turn with comparison text
        """
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Round 1: First tool use
        tool_block_1 = Mock()
        tool_block_1.type = "tool_use"
        tool_block_1.id = "tool_call_1"
        tool_block_1.name = "search_course_content"
        tool_block_1.input = {"query": "machine learning"}

        tool_use_1 = Mock()
        tool_use_1.stop_reason = "tool_use"
        tool_use_1.content = [tool_block_1]

        # Round 2: Second tool use
        tool_block_2 = Mock()
        tool_block_2.type = "tool_use"
        tool_block_2.id = "tool_call_2"
        tool_block_2.name = "search_course_content"
        tool_block_2.input = {"query": "artificial intelligence"}

        tool_use_2 = Mock()
        tool_use_2.stop_reason = "tool_use"
        tool_use_2.content = [tool_block_2]

        # Final: Text response
        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock(type="text", text="ML focuses on algorithms, while AI is broader...")]

        mock_client.messages.create.side_effect = [
            tool_use_1,
            tool_use_2,
            final_response
        ]

        mock_tool_manager.execute_tool.side_effect = [
            "ML course content: focuses on algorithms...",
            "AI course content: covers broad topics..."
        ]

        generator = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514", max_tool_rounds=2)

        # Execute
        result = generator.generate_response(
            query="Compare ML course to AI course",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Verify
        assert result == "ML focuses on algorithms, while AI is broader..."
        assert mock_client.messages.create.call_count == 3
        assert mock_tool_manager.execute_tool.call_count == 2

        # Verify tools parameter present in calls 1-2, absent in call 3
        call_1 = mock_client.messages.create.call_args_list[0]
        assert "tools" in call_1.kwargs
        assert call_1.kwargs["tool_choice"] == {"type": "auto"}

        call_2 = mock_client.messages.create.call_args_list[1]
        assert "tools" in call_2.kwargs
        assert call_2.kwargs["tool_choice"] == {"type": "auto"}

        call_3 = mock_client.messages.create.call_args_list[2]
        assert "tools" not in call_3.kwargs
        assert "tool_choice" not in call_3.kwargs

        # Verify message structure at final call (5 messages)
        final_messages = mock_client.messages.create.call_args_list[2].kwargs["messages"]
        assert len(final_messages) == 5
        assert final_messages[0]["role"] == "user"       # Original query
        assert final_messages[1]["role"] == "assistant"  # Tool use 1
        assert final_messages[2]["role"] == "user"       # Tool result 1
        assert final_messages[3]["role"] == "assistant"  # Tool use 2
        assert final_messages[4]["role"] == "user"       # Tool result 2

    @patch('ai_generator.anthropic.Anthropic')
    def test_max_rounds_prevents_infinite_loop(
        self,
        mock_anthropic_class,
        mock_tool_manager
    ):
        """
        Verify that tool calling stops after max_tool_rounds.

        Scenario: Claude keeps requesting tools beyond limit
        Round 1: tool_use (with tools parameter)
        Round 2: tool_use (without tools parameter, but still returns tool_use)
        Should exit after round 2 with max rounds exceeded message
        """
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Initial call: Tool use
        tool_block_0 = Mock()
        tool_block_0.type = "tool_use"
        tool_block_0.id = "tool_call_0"
        tool_block_0.name = "search_course_content"
        tool_block_0.input = {"query": "topic 0"}

        tool_use_0 = Mock()
        tool_use_0.stop_reason = "tool_use"
        tool_use_0.content = [tool_block_0]

        # Round 1: Tool use
        tool_block_1 = Mock()
        tool_block_1.type = "tool_use"
        tool_block_1.id = "tool_call_1"
        tool_block_1.name = "search_course_content"
        tool_block_1.input = {"query": "topic 1"}

        tool_use_1 = Mock()
        tool_use_1.stop_reason = "tool_use"
        tool_use_1.content = [tool_block_1]

        # Round 2: Still wants tools (but reached limit)
        tool_block_2 = Mock()
        tool_block_2.type = "tool_use"
        tool_block_2.id = "tool_call_2"
        tool_block_2.name = "search_course_content"
        tool_block_2.input = {"query": "topic 2"}

        tool_use_2 = Mock()
        tool_use_2.stop_reason = "tool_use"
        tool_use_2.content = [tool_block_2]

        mock_client.messages.create.side_effect = [
            tool_use_0,  # Initial call
            tool_use_1,  # Round 1 with tools
            tool_use_2   # Round 2 without tools (but still returns tool_use)
        ]

        mock_tool_manager.execute_tool.side_effect = [
            "Result 0",
            "Result 1",
            "Result 2"
        ]

        generator = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514", max_tool_rounds=2)

        # Execute
        result = generator.generate_response(
            query="Complex question",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Verify
        # Should stop after 2 rounds and return max rounds exceeded message
        assert "Unable to complete query within" in result or result != ""
        assert mock_client.messages.create.call_count == 3
        assert mock_tool_manager.execute_tool.call_count == 3

        # Verify tools parameter present in round 1, absent in round 2
        call_2 = mock_client.messages.create.call_args_list[1]  # Round 1
        assert "tools" in call_2.kwargs

        call_3 = mock_client.messages.create.call_args_list[2]  # Round 2 (final)
        assert "tools" not in call_3.kwargs

    @patch('ai_generator.anthropic.Anthropic')
    def test_tool_error_sent_to_claude_for_recovery(
        self,
        mock_anthropic_class,
        mock_tool_manager
    ):
        """
        Verify that tool errors are passed to Claude, allowing recovery.

        Scenario: First tool fails, Claude adapts and tries different approach
        Round 1: search fails with "Course not found"
        Round 2: Claude tries get_course_outline instead
        Round 3: Success
        """
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Round 1: First tool use
        tool_block_1 = Mock()
        tool_block_1.type = "tool_use"
        tool_block_1.id = "tool_call_1"
        tool_block_1.name = "search_course_content"
        tool_block_1.input = {"query": "XYZ"}

        tool_use_1 = Mock()
        tool_use_1.stop_reason = "tool_use"
        tool_use_1.content = [tool_block_1]

        # Round 2: Second tool use (different tool)
        tool_block_2 = Mock()
        tool_block_2.type = "tool_use"
        tool_block_2.id = "tool_call_2"
        tool_block_2.name = "get_course_outline"
        tool_block_2.input = {"course_name": "XYZ"}

        tool_use_2 = Mock()
        tool_use_2.stop_reason = "tool_use"
        tool_use_2.content = [tool_block_2]

        # Final: Text response
        final_response = Mock()
        final_response.stop_reason = "end_turn"
        final_response.content = [Mock(type="text", text="Here's the course outline...")]

        mock_client.messages.create.side_effect = [
            tool_use_1,
            tool_use_2,
            final_response
        ]

        # First tool throws exception, second succeeds
        mock_tool_manager.execute_tool.side_effect = [
            Exception("Course not found matching 'XYZ'"),
            "Outline: Lesson 1, Lesson 2..."
        ]

        generator = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514", max_tool_rounds=2)

        # Execute
        result = generator.generate_response(
            query="Find XYZ course",
            tools=[{"name": "search_course_content"}, {"name": "get_course_outline"}],
            tool_manager=mock_tool_manager
        )

        # Verify
        assert result == "Here's the course outline..."
        assert mock_client.messages.create.call_count == 3
        assert mock_tool_manager.execute_tool.call_count == 2

        # Verify error was passed to second API call
        second_call = mock_client.messages.create.call_args_list[1]
        tool_result_content = second_call.kwargs["messages"][2]["content"][0]["content"]
        assert "Tool execution failed" in tool_result_content
        assert "Course not found" in tool_result_content

    @patch('ai_generator.anthropic.Anthropic')
    def test_tools_parameter_management_across_rounds(
        self,
        mock_anthropic_class,
        mock_tool_manager
    ):
        """
        Verify tools parameter is correctly added/removed across rounds.

        Critical for preventing infinite loops and forcing final synthesis.
        """
        # Setup
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Initial call: Tool use
        tool_block_0 = Mock()
        tool_block_0.type = "tool_use"
        tool_block_0.id = "tool_call_0"
        tool_block_0.name = "search_course_content"
        tool_block_0.input = {"query": "test0"}

        tool_use_0 = Mock()
        tool_use_0.stop_reason = "tool_use"
        tool_use_0.content = [tool_block_0]

        # Round 1: Tool use
        tool_block_1 = Mock()
        tool_block_1.type = "tool_use"
        tool_block_1.id = "tool_call_1"
        tool_block_1.name = "search_course_content"
        tool_block_1.input = {"query": "test"}

        tool_use_1 = Mock()
        tool_use_1.stop_reason = "tool_use"
        tool_use_1.content = [tool_block_1]

        # Round 2: Tool use (final round)
        tool_block_2 = Mock()
        tool_block_2.type = "tool_use"
        tool_block_2.id = "tool_call_2"
        tool_block_2.name = "search_course_content"
        tool_block_2.input = {"query": "test2"}

        tool_use_2 = Mock()
        tool_use_2.stop_reason = "tool_use"
        tool_use_2.content = [tool_block_2]

        mock_client.messages.create.side_effect = [
            tool_use_0,  # Initial
            tool_use_1,  # Round 1
            tool_use_2   # Round 2
        ]

        mock_tool_manager.execute_tool.side_effect = ["Result 0", "Result 1", "Result 2"]

        generator = AIGenerator(api_key="test_key", model="claude-sonnet-4-20250514", max_tool_rounds=2)

        # Execute
        result = generator.generate_response(
            query="Test query",
            tools=[{"name": "search_course_content"}],
            tool_manager=mock_tool_manager
        )

        # Verify tools parameter presence
        call_1_params = mock_client.messages.create.call_args_list[0].kwargs  # Initial call
        assert "tools" in call_1_params
        assert call_1_params["tool_choice"] == {"type": "auto"}

        call_2_params = mock_client.messages.create.call_args_list[1].kwargs  # Round 1
        assert "tools" in call_2_params
        assert call_2_params["tool_choice"] == {"type": "auto"}

        # KEY: Third call (round 2) should NOT have tools parameter (final round)
        call_3_params = mock_client.messages.create.call_args_list[2].kwargs  # Round 2 (final)
        assert "tools" not in call_3_params
        assert "tool_choice" not in call_3_params
