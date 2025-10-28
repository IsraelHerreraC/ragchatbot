# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A full-stack Retrieval-Augmented Generation (RAG) system that answers questions about course materials using semantic search and Anthropic's Claude API. The system processes course documents, stores them in a vector database (ChromaDB), and uses Claude's tool-calling capability to intelligently search and synthesize answers.

## Development Commands

### Running the Application

```bash
# Option 1: Using the run script
./run.sh

# Option 2: Manual start (from project root)
cd backend
uv run uvicorn app:app --reload --port 8000

# Option 3: Using uv run directly (without changing directory)
uv run --directory backend uvicorn app:app --reload --port 8000
```

The application runs on `http://localhost:8000` with API docs at `http://localhost:8000/docs`.

### Dependency Management

**IMPORTANT: Always use `uv` to manage dependencies. Do NOT use `pip` directly.**

```bash
# Install/sync dependencies (uses uv package manager)
uv sync

# Add a new dependency
uv add package-name

# Remove a dependency
uv remove package-name

# Update dependencies
uv lock --upgrade

# Run Python scripts/commands with uv
uv run python script.py
uv run uvicorn app:app --reload
```

### Environment Setup

Required `.env` file in project root:
```
ANTHROPIC_API_KEY=your-api-key-here
```

## Architecture

### High-Level Flow

```
User Query � FastAPI � RAG System � AI Generator � Claude API (decides to use tool)
                                                          �
                                               Tool Manager executes search
                                                          �
                                    Vector Store (semantic search in ChromaDB)
                                                          �
                                    Search results returned to Claude API
                                                          �
                                    Claude synthesizes answer � Response + Sources
```

### Component Orchestration

**RAGSystem** (`rag_system.py`) is the central orchestrator that coordinates:
- `DocumentProcessor` - Parses course files, extracts metadata, chunks text
- `VectorStore` - Manages ChromaDB collections and semantic search
- `AIGenerator` - Handles Claude API interactions with tool support
- `SessionManager` - Maintains conversation history (in-memory)
- `ToolManager` - Registers and executes tools (currently: `CourseSearchTool`)

### Two-Phase Claude API Pattern

The system makes **two API calls** for tool-based queries:

1. **First call**: Claude receives query + tool definitions � returns tool_use request
2. **Tool execution**: Python executes search, formats results
3. **Second call**: Claude receives tool results � synthesizes final answer

This is implemented in `ai_generator.py:_handle_tool_execution()`.

### Vector Store Architecture

ChromaDB uses **two collections**:
- `course_catalog` - Course/lesson metadata for fuzzy course name matching
- `course_content` - Text chunks (800 chars with 100 char overlap) with embeddings

Search flow: `VectorStore.search()` � `_resolve_course_name()` (fuzzy match) � `_build_filter()` � semantic search on `course_content`.

### Document Processing Pipeline

Course documents must follow this format:
```
Course Title: [title]
Course Link: [url]
Course Instructor: [name]

Lesson 0: [lesson title]
Lesson Link: [url]
[lesson content...]
```

Processing happens automatically on startup (`app.py:startup_event`):
1. Read files from `docs/` folder
2. Extract course/lesson metadata (regex-based parsing)
3. Chunk lesson content (sentence-based, 800 chars with 100 overlap)
4. Generate embeddings using `all-MiniLM-L6-v2`
5. Store in ChromaDB with metadata (course_title, lesson_number, chunk_index)

**Duplicate Prevention**: `add_course_folder()` checks existing course titles before processing.

### Session Management

Sessions are **in-memory only** (not persisted):
- Created on first query if no session_id provided
- Stores last `MAX_HISTORY` (default: 2) conversation exchanges
- History is formatted as string and passed to Claude's system prompt
- Session IDs follow pattern: `session_{counter}`

### Tool System Design

Tools inherit from `Tool` abstract base class (`search_tools.py`):
- `get_tool_definition()` - Returns Anthropic tool schema
- `execute(**kwargs)` - Performs tool action

`CourseSearchTool` tracks `last_sources` which are retrieved after query completion and sent to frontend for display.

### Configuration

All settings centralized in `config.py`:
- `ANTHROPIC_MODEL`: claude-sonnet-4-20250514
- `EMBEDDING_MODEL`: all-MiniLM-L6-v2
- `CHUNK_SIZE`: 800 (characters per chunk)
- `CHUNK_OVERLAP`: 100 (overlap between chunks)
- `MAX_RESULTS`: 5 (search results to return)
- `MAX_HISTORY`: 2 (conversation exchanges to remember)
- `CHROMA_PATH`: ./chroma_db

## Important Patterns

### Adding New Course Documents

Place files in `docs/` directory (supports .txt, .pdf, .docx). Documents are auto-processed on server startup. To force re-processing:
```python
rag_system.add_course_folder("../docs", clear_existing=True)
```

### Adding New Tools

1. Create tool class inheriting from `Tool` in `search_tools.py`
2. Implement `get_tool_definition()` and `execute()`
3. Register in `RAGSystem.__init__()`:
```python
new_tool = YourNewTool(dependencies)
self.tool_manager.register_tool(new_tool)
```

### Modifying Claude's Behavior

Edit the static `SYSTEM_PROMPT` in `ai_generator.py:8-30`. Current prompt emphasizes:
- Use search tool only for course-specific questions
- One search per query maximum
- No meta-commentary in responses
- Brief, concise, educational tone

### ChromaDB Persistence

Data persists in `backend/chroma_db/` directory. To reset:
```python
rag_system.vector_store.clear_all_data()
```
Or manually delete the directory.

## Data Models

Core Pydantic models in `models.py`:
- `Course` - title (used as unique ID), course_link, instructor, lessons[]
- `Lesson` - lesson_number, title, lesson_link
- `CourseChunk` - content, course_title, lesson_number, chunk_index

## Frontend-Backend Contract

### POST /api/query
Request:
```json
{
  "query": "user question",
  "session_id": "session_1" // optional, created if null
}
```

Response:
```json
{
  "answer": "AI response text",
  "sources": ["Course Title - Lesson 0", ...],
  "session_id": "session_1"
}
```

### GET /api/courses
Returns:
```json
{
  "total_courses": 4,
  "course_titles": ["Course 1", "Course 2", ...]
}
```

## Known Limitations

- No test suite exists
- Sessions are not persisted (lost on server restart)
- No authentication/authorization
- In-memory session storage doesn't scale
- Document processing happens synchronously on startup
- No pagination for course content retrieval
- Chunk prefix inconsistency: early lessons use "Lesson X content:", last lesson uses "Course [title] Lesson X content:" (see `document_processor.py:186` vs `234`)

## Files to Check When...

**Modifying search behavior**: `vector_store.py` (search logic), `search_tools.py` (tool definition)

**Changing Claude's responses**: `ai_generator.py` (system prompt, API params)

**Adjusting document parsing**: `document_processor.py` (regex patterns, chunking algorithm)

**Adding API endpoints**: `app.py` (FastAPI routes)

**Changing frontend UI**: `frontend/index.html`, `frontend/style.css`, `frontend/script.js`

**Tuning performance**: `config.py` (chunk sizes, max results, history length)
- When adding or commiting, do not include in the description information related to Claude Code