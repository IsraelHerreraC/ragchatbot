import anthropic
from typing import List, Optional, Dict, Any

class AIGenerator:
    """Handles interactions with Anthropic's Claude API for generating responses"""
    
    # Static system prompt to avoid rebuilding on each call
    SYSTEM_PROMPT = """ You are an AI assistant specialized in course materials and educational content with access to tools for searching course information and retrieving course outlines.

Tool Usage Guidelines:
- **search_course_content**: Use for questions about specific course content or detailed educational materials
- **get_course_outline**: Use for questions about course structure, lesson list, or course overview
- **Sequential tool use**: You may use tools in sequence (max 2 rounds) if needed to answer comprehensively
  * Use first tool call to gather initial information
  * Use second tool call only if the first results indicate you need additional/different data
  * Examples of valid sequential use:
    - Get course outline, then search specific lesson content
    - Search one course, then search another for comparison
    - Search broad topic, then narrow search based on findings
- **Tool efficiency**: Prefer single tool call when possible
- Synthesize tool results into accurate, fact-based responses
- If tool yields no results, state this clearly without offering alternatives

Response Protocol:
- **General knowledge questions**: Answer using existing knowledge without using tools
- **Course content questions**: Use search_course_content tool first, then answer
- **Course outline questions**: Use get_course_outline tool to retrieve course title, course link, lesson count, and complete lesson list (with lesson numbers and titles)
- **No meta-commentary**:
 - Provide direct answers only — no reasoning process, tool usage explanations, or question-type analysis
 - Do not mention "based on the search results", "I used two searches", or "based on the course outline"


All responses must be:
1. **Brief, Concise and focused** - Get to the point quickly
2. **Educational** - Maintain instructional value
3. **Clear** - Use accessible language
4. **Example-supported** - Include relevant examples when they aid understanding
Provide only the direct answer to what was asked.
"""
    
    def __init__(self, api_key: str, model: str, max_tool_rounds: int = 2):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tool_rounds = max_tool_rounds

        # Pre-build base API parameters
        self.base_params = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 800
        }
    
    def generate_response(self, query: str,
                         conversation_history: Optional[str] = None,
                         tools: Optional[List] = None,
                         tool_manager=None) -> str:
        """
        Generate AI response with optional tool usage and conversation context.
        
        Args:
            query: The user's question or request
            conversation_history: Previous messages for context
            tools: Available tools the AI can use
            tool_manager: Manager to execute tools
            
        Returns:
            Generated response as string
        """
        
        # Build system content efficiently - avoid string ops when possible
        system_content = (
            f"{self.SYSTEM_PROMPT}\n\nPrevious conversation:\n{conversation_history}"
            if conversation_history 
            else self.SYSTEM_PROMPT
        )
        
        # Prepare API call parameters efficiently
        api_params = {
            **self.base_params,
            "messages": [{"role": "user", "content": query}],
            "system": system_content
        }
        
        # Add tools if available
        if tools:
            api_params["tools"] = tools
            api_params["tool_choice"] = {"type": "auto"}
        
        # Get response from Claude
        response = self.client.messages.create(**api_params)
        
        # Handle tool execution if needed
        if response.stop_reason == "tool_use" and tool_manager:
            return self._handle_tool_execution(response, api_params, tool_manager, tools_available=tools)
        
        # Return direct response
        return response.content[0].text

    def _extract_text_response(self, response) -> str:
        """
        Extract text content from API response.
        Handles responses with mixed content blocks.
        """
        for content_block in response.content:
            if hasattr(content_block, 'type') and content_block.type == "text":
                return content_block.text
        return "Error: No text content in response"

    def _handle_max_rounds_exceeded(self, response, rounds_used: int) -> str:
        """
        Handle case where max tool rounds exceeded but Claude still wants tools.

        Options:
        1. Return explanatory message to user
        2. Extract any text content from last response
        3. Make one final call without tools
        """
        # Try to extract any text from current response
        text = self._extract_text_response(response)
        if text and not text.startswith("Error:"):
            return text

        # Otherwise return informative message
        return (
            f"Unable to complete query within {rounds_used} tool rounds. "
            "Please try rephrasing your question or breaking it into smaller parts."
        )

    def _handle_tool_execution(self, initial_response, base_params: Dict[str, Any], tool_manager, tools_available: Optional[List] = None):
        """
        Handle sequential tool execution with loop-based architecture.

        Args:
            initial_response: The response containing tool use requests
            base_params: Base API parameters
            tool_manager: Manager to execute tools
            tools_available: Available tools the AI can use

        Returns:
            Final response text after all tool rounds complete
        """
        # Initialize message history and round counter
        messages = base_params["messages"].copy()
        current_response = initial_response
        round_counter = 0  # Will increment to 1 on first iteration

        # MAIN LOOP: Continue until terminal condition
        while True:
            # --- TERMINATION CONDITIONS ---

            # Check if current response is NOT tool_use
            if current_response.stop_reason != "tool_use":
                # Extract and return final text
                return self._extract_text_response(current_response)

            # --- TOOL EXECUTION PHASE ---

            # Add assistant's tool_use response to message history
            messages.append({
                "role": "assistant",
                "content": current_response.content
            })

            # Execute all requested tools and collect results
            tool_results = []

            for content_block in current_response.content:
                if content_block.type == "tool_use":
                    try:
                        result = tool_manager.execute_tool(
                            content_block.name,
                            **content_block.input
                        )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": result
                        })
                    except Exception as e:
                        # Track errors but continue with other tools
                        error_msg = f"Tool execution failed: {str(e)}"
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": error_msg,
                            "is_error": True
                        })

            # If no tools were executed, something is wrong
            if not tool_results:
                return "Error: Tool use requested but no tools executed"

            # Add tool results to message history
            messages.append({
                "role": "user",
                "content": tool_results
            })

            # --- NEXT API CALL PHASE ---

            # Increment round counter BEFORE making the call
            # This represents "which round we're about to execute"
            round_counter += 1

            # Check if we've hit the limit BEFORE making another API call
            if round_counter > self.max_tool_rounds:
                # We've completed max_tool_rounds, don't make another call
                return self._handle_max_rounds_exceeded(current_response, self.max_tool_rounds)

            # Build API parameters
            api_params = {
                **self.base_params,
                "messages": messages,
                "system": base_params["system"]
            }

            # KEY DECISION: Add tools parameter only if not at final round
            # round_counter now represents the current round (1, 2, 3...)
            # We allow tools only if round_counter < max_tool_rounds
            if round_counter < self.max_tool_rounds and tools_available:
                api_params["tools"] = tools_available
                api_params["tool_choice"] = {"type": "auto"}
            # else: no tools parameter = forces text response

            # Make next API call
            try:
                current_response = self.client.messages.create(**api_params)
            except Exception as e:
                return f"API error in round {round_counter}: {str(e)}"