# RAG Chatbot Query Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   FRONTEND                                       │
│                              (script.js / browser)                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                    User types: "What is computer use?"
                                      │
                         ┌────────────▼────────────┐
                         │  sendMessage()          │
                         │  - Disable input        │
                         │  - Show user message    │
                         │  - Show loading dots    │
                         └────────────┬────────────┘
                                      │
                    POST /api/query   │
                    ┌─────────────────▼─────────────────┐
                    │ Body: {                           │
                    │   query: "What is computer use?", │
                    │   session_id: null                │
                    │ }                                 │
                    └─────────────────┬─────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   BACKEND                                        │
│                                  (FastAPI)                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │ app.py:query_documents()│
                         │ - Validate request      │
                         │ - Create/get session    │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌────────────────────────────────────┐
                         │ session_manager.create_session()   │
                         │ Returns: "abc-123-def"             │
                         └────────────┬───────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               RAG SYSTEM                                         │
│                           (rag_system.py)                                        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                         ┌────────────▼────────────┐
                         │ rag_system.query()      │
                         │ - Get history (if any)  │
                         │ - Prepare prompt        │
                         └────────────┬────────────┘
                                      │
                         Prompt: "Answer this question about
                                course materials: What is computer use?"
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             AI GENERATOR                                         │
│                          (ai_generator.py)                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                         ┌────────────▼─────────────────────────┐
                         │ generate_response()                  │
                         │ - Build system prompt + history      │
                         │ - Add tool definitions               │
                         │ - Prepare API params                 │
                         └────────────┬─────────────────────────┘
                                      │
                    ══════════════════╪══════════════════
                       ANTHROPIC API CALL #1
                    ══════════════════╪══════════════════
                                      │
                         ┌────────────▼─────────────────────────┐
                         │ anthropic.messages.create()          │
                         │ - model: claude-sonnet-4             │
                         │ - temperature: 0                     │
                         │ - max_tokens: 800                    │
                         │ - system: [instructions]             │
                         │ - messages: [user query]             │
                         │ - tools: [search_course_content]     │
                         │ - tool_choice: auto                  │
                         └────────────┬─────────────────────────┘
                                      │
                         ┌────────────▼─────────────────────────┐
                         │ CLAUDE THINKS:                       │
                         │ "This is about course content,       │
                         │  I need to search for information    │
                         │  about computer use"                 │
                         └────────────┬─────────────────────────┘
                                      │
                      Response: stop_reason = "tool_use"
                                      │
                         ┌────────────▼─────────────────────────┐
                         │ Tool Call Request:                   │
                         │ {                                    │
                         │   name: "search_course_content",     │
                         │   input: {                           │
                         │     query: "computer use capability",│
                         │     course_name: "Computer Use"      │
                         │   }                                  │
                         │ }                                    │
                         └────────────┬─────────────────────────┘
                                      │
                         ┌────────────▼─────────────────────────┐
                         │ _handle_tool_execution()             │
                         │ - Collect tool use blocks            │
                         │ - Execute each tool                  │
                         └────────────┬─────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             TOOL MANAGER                                         │
│                          (search_tools.py)                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                         ┌────────────▼─────────────────────────┐
                         │ tool_manager.execute_tool()          │
                         │ - Find tool: "search_course_content" │
                         │ - Call CourseSearchTool.execute()    │
                         └────────────┬─────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                             VECTOR STORE                                         │
│                           (vector_store.py)                                      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
         ┌──────────▼──────────┐     │     ┌──────────▼──────────┐
         │ STEP 1: Resolve     │     │     │ CHROMADB            │
         │ Course Name         │     │     │                     │
         │                     │     │     │ ┌─────────────────┐ │
         │ Query catalog:      │     │     │ │ course_catalog  │ │
         │ "Computer Use"      │     │     │ │  - metadata     │ │
         │                     │     │     │ │  - titles       │ │
         │ Returns:            │     │     │ └─────────────────┘ │
         │ "Building Towards   │     │     │                     │
         │  Computer Use with  │     │     │ ┌─────────────────┐ │
         │  Anthropic"         │     │     │ │ course_content  │ │
         └──────────┬──────────┘     │     │ │  - 800char      │ │
                    │                │     │ │    chunks       │ │
         ┌──────────▼──────────┐     │     │ │  - embeddings   │ │
         │ STEP 2: Build Filter│     │     │ │  - metadata     │ │
         │                     │     │     │ └─────────────────┘ │
         │ where = {           │     │     │                     │
         │   "course_title":   │     │     │ Embedding Model:    │
         │   "Building..."     │     │     │ all-MiniLM-L6-v2    │
         │ }                   │     │     └─────────────────────┘
         └──────────┬──────────┘     │
                    │                │
         ┌──────────▼──────────────────────────────┐
         │ STEP 3: Semantic Search                 │
         │                                          │
         │ 1. Convert query to embedding vector    │
         │    "computer use capability" → [0.23... │
         │                                          │
         │ 2. Compare with stored embeddings       │
         │    (cosine similarity)                  │
         │                                          │
         │ 3. Return top 5 matches                 │
         └──────────┬──────────────────────────────┘
                    │
         ┌──────────▼──────────────────────────────┐
         │ Results:                                 │
         │ - Chunk 1: "That is, it can look at..." │
         │   Meta: {course: "Building...", lesson:0}│
         │ - Chunk 2: "This computer use..."       │
         │   Meta: {course: "Building...", lesson:0}│
         │ - Chunk 3: "...enable computer use."    │
         │   Meta: {course: "Building...", lesson:0}│
         │ - ... (up to 5 chunks)                   │
         └──────────┬──────────────────────────────┘
                    │
                    ▼
         ┌─────────────────────────────────────────┐
         │ CourseSearchTool._format_results()      │
         │                                          │
         │ Output:                                  │
         │ "[Building... - Lesson 0]                │
         │  That is, it can look at the screen...  │
         │                                          │
         │  [Building... - Lesson 0]                │
         │  This computer use capability is..."     │
         │                                          │
         │ Also stores:                             │
         │ last_sources = [                         │
         │   "Building... - Lesson 0",              │
         │   "Building... - Lesson 0"               │
         │ ]                                        │
         └──────────┬──────────────────────────────┘
                    │
                    │ Return formatted results
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AI GENERATOR (continued)                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                    │
         ┌──────────▼──────────────────────────────┐
         │ Build messages array:                   │
         │ [                                        │
         │   {role: "user",                         │
         │    content: "Answer this question..."},  │
         │   {role: "assistant",                    │
         │    content: [tool_use block]},           │
         │   {role: "user",                         │
         │    content: [tool_result with context]}  │
         │ ]                                        │
         └──────────┬──────────────────────────────┘
                    │
                    │
                ══════════════════════════════════════
                   ANTHROPIC API CALL #2
                ══════════════════════════════════════
                    │
         ┌──────────▼──────────────────────────────┐
         │ anthropic.messages.create()              │
         │ - Same params as before                  │
         │ - BUT messages now include search results│
         │ - NO tools this time                     │
         └──────────┬──────────────────────────────┘
                    │
         ┌──────────▼──────────────────────────────┐
         │ CLAUDE SYNTHESIZES:                      │
         │ "Computer use is a capability that       │
         │  allows the model to control a computer  │
         │  by taking screenshots and generating    │
         │  mouse clicks or keystrokes..."          │
         │                                          │
         │ (Based on search results)                │
         └──────────┬──────────────────────────────┘
                    │
                    │ Return response.content[0].text
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          RAG SYSTEM (continued)                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                    │
         ┌──────────▼──────────────────────────────┐
         │ After AI response:                       │
         │                                          │
         │ 1. sources = tool_manager.get_last_      │
         │    sources()                             │
         │    → ["Building... - Lesson 0"]          │
         │                                          │
         │ 2. tool_manager.reset_sources()          │
         │                                          │
         │ 3. session_manager.add_exchange(         │
         │      session_id, query, response)        │
         │    Stores for future context             │
         │                                          │
         │ 4. return (response, sources)            │
         └──────────┬──────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            FASTAPI (continued)                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                    │
         ┌──────────▼──────────────────────────────┐
         │ Build QueryResponse:                     │
         │ {                                        │
         │   "answer": "Computer use is...",        │
         │   "sources": ["Building... - Lesson 0"], │
         │   "session_id": "abc-123-def"            │
         │ }                                        │
         └──────────┬──────────────────────────────┘
                    │
                    │ HTTP 200 OK
                    │ Content-Type: application/json
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (continued)                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
                    │
         ┌──────────▼──────────────────────────────┐
         │ Receive JSON response                    │
         │                                          │
         │ 1. const data = await response.json()   │
         │                                          │
         │ 2. Save session ID:                      │
         │    currentSessionId = data.session_id    │
         │                                          │
         │ 3. Remove loading dots                   │
         │                                          │
         │ 4. addMessage(data.answer, 'assistant',  │
         │               data.sources)              │
         │                                          │
         │ 5. Render markdown with marked.parse()   │
         │                                          │
         │ 6. Add collapsible sources section       │
         │                                          │
         │ 7. Re-enable input                       │
         └──────────┬──────────────────────────────┘
                    │
                    ▼
         ┌─────────────────────────────────────────┐
         │         FINAL UI DISPLAY                 │
         │                                          │
         │  ┌────────────────────────────────────┐ │
         │  │ User                               │ │
         │  │ What is computer use?              │ │
         │  └────────────────────────────────────┘ │
         │                                          │
         │  ┌────────────────────────────────────┐ │
         │  │ Assistant                          │ │
         │  │ Computer use is a capability that  │ │
         │  │ allows the model to control a      │ │
         │  │ computer by taking screenshots...  │ │
         │  │                                    │ │
         │  │ ▶ Sources                          │ │
         │  │   Building Towards Computer Use... │ │
         │  │   - Lesson 0                       │ │
         │  └────────────────────────────────────┘ │
         │                                          │
         │  [Type your message...]         [Send]  │
         └─────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
                              KEY COMPONENTS
═══════════════════════════════════════════════════════════════════════════════

┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   SESSION MGR    │     │  DOCUMENT PROC   │     │    CONFIG        │
│                  │     │                  │     │                  │
│ - Create UUID    │     │ - Parse docs     │     │ - API keys       │
│ - Store history  │     │ - Extract meta   │     │ - Model name     │
│ - Max 2 exchanges│     │ - Chunk text     │     │ - Chunk size     │
└──────────────────┘     └──────────────────┘     └──────────────────┘


═══════════════════════════════════════════════════════════════════════════════
                              DATA FLOW SUMMARY
═══════════════════════════════════════════════════════════════════════════════

1. User Query (Frontend) ────────────────┐
                                         │
2. HTTP POST ─────────────────────────►  │
                                         │
3. FastAPI Endpoint ──────────────────►  │
                                         │
4. RAG System Orchestrator ───────────►  │
                                         │
5. AI Generator + System Prompt ──────►  │  ORCHESTRATION
                                         │      LAYER
6. Claude API #1 (tool decision) ─────►  │
                                         │
7. Tool Execution Request ────────────►  │
                                         │
8. Vector Search (ChromaDB) ──────────►  │
                                         │
9. Return Search Results ─────────────►  │
                                         │
10. Claude API #2 (synthesis) ────────►  │
                                         │
11. Update Session History ───────────►  │
                                         │
12. Return JSON to Frontend ──────────►  │
                                         │
13. Display Answer + Sources ─────────►  │
                                         │
14. Ready for Next Query ─────────────►  │
                                         ▼

═══════════════════════════════════════════════════════════════════════════════
                          PERFORMANCE METRICS
═══════════════════════════════════════════════════════════════════════════════

Typical Query Timeline:
├─ Frontend: 10-50ms (UI updates)
├─ Network: 20-100ms (API request)
├─ Session Check: <5ms
├─ Claude API #1: 500-2000ms (tool decision)
├─ Vector Search: 50-200ms (embedding + similarity)
├─ Claude API #2: 1000-3000ms (synthesis)
├─ Session Update: <5ms
└─ Frontend Render: 10-50ms

Total: ~2-6 seconds per query (with tool use)
       ~1-3 seconds (direct answer without tools)

Vector Database:
- 344KB course content → ~hundreds of 800-char chunks
- Embedding dimension: 384 (all-MiniLM-L6-v2)
- Max results returned: 5 chunks
- Search method: Cosine similarity

API Constraints:
- Max tokens: 800
- Temperature: 0 (deterministic)
- Model: claude-sonnet-4-20250514
```
