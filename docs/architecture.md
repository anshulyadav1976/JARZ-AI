# Architecture (JARZ-AI / RentRadar)

This doc is intended for hackathon judges and teammates who want to understand **how the system works end-to-end**.

## High-level overview

```mermaid
flowchart LR
  U[User in browser] -->|chat message| FE[Next.js Frontend]
  FE -->|SSE POST /api/chat/stream| BE[FastAPI Backend]
  BE -->|OpenRouter - OpenAI compatible| LLM[LLM]
  BE -->|HTTP optional| SS[ScanSan API]
  BE -->|SQLite| DB[(chat.db)]
  BE -->|JSON TTL cache| C[(backend/cache.json)]

  BE -->|SSE events: text + a2ui + complete| FE
  FE -->|A2UI render| UI[Insights side panel]
```

## Runtime components

- **Frontend (Next.js)**: `frontend/`
  - Owns the UX: chat, sidebar tabs, A2UI renderer, charts, tables, maps.
  - Consumes **Server‑Sent Events (SSE)** from the backend so chat + UI updates stream live.

- **Backend (FastAPI + LangGraph)**: `backend/app/`
  - Exposes `/api/chat/stream` and other data endpoints.
  - Runs the **LangGraph chat agent** which can call tools.
  - Persists conversations/messages into SQLite.
  - Caches tool + ScanSan responses to disk for fast demos.

- **External services**
  - **OpenRouter** for LLM calls (OpenAI-compatible API).
  - **ScanSan** for property/market datasets (optional toggle via `USE_SCANSAN`).
  - **Mapbox** (optional) for Property Finder map view.

## Chat streaming (SSE) contract

The frontend expects **SSE frames** of the form:

```
event: <name>
data: <single-line JSON>

```

Event types used by the chat stream:

```mermaid
sequenceDiagram
  participant FE as Frontend
  participant BE as Backend
  participant LG as LangGraph Chat Graph
  participant LLM as LLM
  participant SS as ScanSan optional

  FE->>BE: POST /api/chat/stream
  BE->>LG: stream_chat_agent
  BE-->>FE: event status
  LG->>LLM: prompt + tool schemas
  LLM-->>LG: tool_calls OR final text
  alt tool_calls
    BE-->>FE: event tool_start
    LG->>SS: call ScanSan endpoints
    LG-->>BE: tool result
    BE-->>FE: event a2ui
    BE-->>FE: event tool_end
    LG->>LLM: follow-up with tool output
  end
  BE-->>FE: event text streamed
  BE-->>FE: event complete
```

## LangGraph: what graphs exist

There are two flows in `backend/app/agent/graph.py`:

1. **Pipeline graph** (legacy valuation workflow): a linear chain:
   `resolve_location → fetch_data → build_features → predict → explain → render_a2ui`

2. **Chat graph** (main UX): loops tool calls as needed:
   `chat → (tool_executor → chat)* → end`

### Visual: pipeline graph

```mermaid
flowchart LR
  A[resolve_location] --> B[fetch_data]
  B --> C[build_features]
  C --> D[predict]
  D --> E[explain]
  E --> F[render_a2ui]
  F --> END((END))
```

### Visual: chat graph (tool loop)

```mermaid
flowchart LR
  C[chat node] -->|tool calls?| T[tool_executor node]
  T --> C
  C -->|final response| END((END))
```

## Data-flow for market data tab

Market Data (growth/demand/valuations/sale history) is loaded via backend endpoints which proxy ScanSan and normalize/shape data for the UI:

```mermaid
flowchart TB
  FE[MarketDataPanel] -->|GET district growth| BE
  FE -->|GET district rent demand| BE
  FE -->|GET district sale demand| BE
  FE -->|GET postcode valuations current| BE
  FE -->|GET postcode valuations historical| BE
  FE -->|GET postcode sale history| BE
  BE --> SS[ScanSan API]
  SS --> BE
  BE -->|JSON responses| FE
```

## Persistence + caching

- **Chat history (SQLite)**: `backend/app/chat.db` by default
  - Conversations + messages are persisted so chat history survives reloads.
  - Assistant messages can include an `a2ui_snapshot` (so the side panel can be restored when reopening a conversation).

- **Cache (JSON TTL)**: `backend/cache.json`
  - Caches:
    - tool outputs (e.g. `tool:[...]`)
    - ScanSan raw API responses (prefixed `scansan:`)
  - Purpose: repeated demo actions become instant, even after backend restart.

