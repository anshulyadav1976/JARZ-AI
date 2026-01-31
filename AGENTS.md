# AGENTS.md — How to work on JARZ-AI safely

This file is written for **humans and coding agents** contributing to this repo.

The goal is simple: **don’t break the demo** (chat streaming + A2UI side panel), and keep model code clearly marked as **PLACEHOLDER** until the teammate’s trained model is plugged in.

---

## Golden rules (must follow)

1. **Do not edit `plan.md`** unless the human explicitly asks.
2. **Never commit secrets** (`.env`, `.env.local`, API keys).
3. **Avoid “invisible breakage”**:
   - If you change backend SSE event names/payloads, you MUST update the frontend SSE parser.
   - If you change A2UI component schemas, you MUST update `A2UIRenderer` (and its wrappers).
4. **Model code is PLACEHOLDER**:
   - Keep `backend/app/model_adapter.py` adapters clearly labeled PLACEHOLDER.
   - Do not implement training here (teammate owns the real model).
5. **Keep the system runnable**:
   - Backend runs on `:8001` by default on Windows (port 8000 may be blocked).
   - Frontend runs on `:3000`.

---

## Project architecture (high-level)

### Backend: FastAPI + LangGraph

- **FastAPI entrypoint**: `backend/app/main.py`
  - `/api/chat/stream`: SSE stream of assistant text + A2UI messages (main UI path)
  - `/api/chat`: non-streaming chat (debug)
  - `/api/query` + `/api/stream`: legacy non-chat pipeline endpoints

- **LangGraph chat agent**
  - `backend/app/agent/state.py`: chat state shape
  - `backend/app/agent/nodes.py`:
    - `chat_node`: calls the LLM, decides “respond” vs “tool call”
    - `tool_executor_node`: runs tool calls, streams tool status and A2UI messages
  - `backend/app/agent/graph.py`: graph wiring + streaming event generation

- **LLM integration (OpenRouter)**
  - `backend/app/llm_client.py`: OpenAI-compatible client targeting OpenRouter
  - `backend/app/config.py`: loads `OPENROUTER_API_KEY`, `LLM_MODEL`, `LLM_BASE_URL`

- **A2UI**
  - `backend/app/a2ui_builder.py`: builds A2UI message sequences
  - The frontend renders A2UI via a component registry.

### Frontend: Next.js (chat + A2UI side panel)

- `frontend/app/page.tsx`: split view (chat left, insights right)
- `frontend/hooks/useChatStream.ts`: consumes `/api/chat/stream` SSE
- `frontend/components/A2UIRenderer.tsx`: maps A2UI components → React UI
- `frontend/components/*`: minimal visualization components (Summary, Chart, Map, Drivers, WhatIf)

---

## Environment setup (source of truth)

### Backend env

Backend loads env from:
- `backend/.env` (preferred)
- repo-root `.env` (supported)

Minimum required to make chat work:

- `OPENROUTER_API_KEY=...`
- `LLM_MODEL=openai/gpt-5-nano`
- `LLM_BASE_URL=https://openrouter.ai/api/v1`

ScanSan (optional for demo stability):

- `USE_SCANSAN=false` (recommended for hackathon demo reliability)
- `SCANSAN_API_KEY=...` (only if enabling ScanSan)

### Frontend env

Set the backend URL:

- `frontend/.env.local`
  - `NEXT_PUBLIC_API_URL=http://localhost:8001`

---

## Streaming contract (backend ↔ frontend)

### Backend → frontend (SSE)

The frontend expects **Server-Sent Events** with:

- `event: <name>`
- `data: <single-line JSON>`
- blank line separating events

Current event names:

- `status` → `{ "node": string, "status": string }`
- `text` → `{ "content": string }`
- `tool_start` → `{ "tool": string, "arguments": any }`
- `tool_end` → `{ "tool": string, "success": boolean }`
- `a2ui` → A2UI message object (e.g. `{ surfaceUpdate: ... }`)
- `error` → `{ "error": string }`
- `complete` → `{ "status": "complete" }`

### CRLF note (Windows)

SSE frames often arrive as `\r\n`. The frontend must `trim()` the `data:` payload before `JSON.parse()`.

If you change parsing logic, re-test on Windows.

---

## How to add a new LangGraph tool (backend)

Most features should be implemented as tools that the LLM can call.

### Step-by-step

1. **Add tool schema** in `backend/app/agent/tools.py`:
   - Add an entry to `TOOL_DEFINITIONS` (OpenAI function calling schema).

2. **Implement the tool**
   - Add `execute_<tool_name>(...)` in `backend/app/agent/tools.py`.
   - Keep return values JSON-serializable.
   - If the tool drives UI updates, return `a2ui_messages: list[dict]`.

3. **Wire it into the dispatcher**
   - Update `execute_tool(...)` in `backend/app/agent/tools.py` to call your new function.

4. **Update the system prompt if needed**
   - `backend/app/agent/nodes.py` (`SYSTEM_PROMPT`) should mention the tool only if it improves tool selection.

5. **Don’t break streaming**
   - Tool execution status is streamed via `tool_start` / `tool_end`.
   - A2UI messages are streamed via the `a2ui` event.

### Tool return shape guidelines

Recommended keys when a tool generates a valuation:
- `prediction`
- `explanation`
- `location`
- `neighbors`
- `a2ui_messages`
- `summary` (short natural-language summary for the LLM)

---

## How to add a new A2UI component (backend + frontend)

### Backend

1. Update `backend/app/a2ui_builder.py` to emit:
   - a `surfaceUpdate` for the component
   - required `dataModelUpdate` paths/values
   - and ensure `beginRendering` points to a root that includes it

2. Keep component `type` stable (example: `SummaryCard`, `DriversBar`).

### Frontend

1. Create a React component in `frontend/components/<ComponentName>.tsx`
2. Add a wrapper + registry entry in `frontend/components/A2UIRenderer.tsx`
3. If you add new prop/data shapes, update `frontend/lib/types.ts`

### Rule of thumb

If you change *any* of these:
- component name
- prop keys
- data model paths

…update both sides together and verify the UI still renders.

---

## Common safe workflows

### Backend dev

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8001
```

### Frontend dev

```powershell
cd frontend
npm run dev
```

---

## Debug checklist (when “chat shows nothing”)

1. Backend logs:
   - Do you see `/api/chat/stream` returning 200?
   - Any `OPENROUTER_API_KEY` errors (e.g. `Bearer ` / illegal header)?
2. Browser console:
   - Any `Failed to parse SSE data` errors?
3. Ensure frontend env points to correct backend:
   - `NEXT_PUBLIC_API_URL=http://localhost:8001`

---

## Git hygiene (please follow)

Do not commit:
- `frontend/.next/`
- `backend/**/__pycache__/`, `**/*.pyc`
- `backend/venv/`, `venv/`
- `.env`, `.env.local`

If you see these in `git status`, fix `.gitignore` / remove from tracking before merging.

