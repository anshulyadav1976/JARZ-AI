# API Reference (Backend + ScanSan)

This repo has **two kinds of APIs**:

- **Backend API** (FastAPI): what the frontend calls.
- **ScanSan API** (external): what the backend calls for market/property data.

> Source of truth for ScanSan endpoints: `api-1.json` (repo root) and ScanSan docs: `https://docs.scansan.com/v1/docs`.

## Backend API (FastAPI)

Backend entrypoint: `backend/app/main.py`

### Chat + UI streaming

- `POST /api/chat/stream`
  - **Purpose**: main chat endpoint used by the frontend. Streams assistant text and A2UI events.
  - **Request**:
    - `message: string`
    - `conversation_id?: string` (to continue a prior chat)
    - `profile?: { name?, role?, bio?, interests?, preferences? }` (personalization)
  - **Response**: `text/event-stream` (SSE)
    - emits events like `status`, `text`, `tool_start`, `tool_end`, `a2ui`, `error`, `complete`.

### Chat history (SQLite)

- `GET /api/conversations`
  - List conversation headers (recent first).

- `GET /api/conversations/{conversation_id}`
  - Fetch a full conversation with messages (including `a2ui_snapshot` on assistant messages).

### Market data proxy endpoints

These endpoints call ScanSan through `backend/app/scansan_client.py`, and benefit from persistent caching.

- `GET /api/district/{district}/growth`
- `GET /api/district/{district}/rent/demand`
  - query params: `period?`, `additional_data?`
- `GET /api/district/{district}/sale/demand`
  - query params: `period?`, `additional_data?`
- `GET /api/postcode/{postcode}/valuations/current`
- `GET /api/postcode/{postcode}/valuations/historical`
- `GET /api/postcode/{postcode}/sale/history`
  - (Used for the export/download flow in the UI.)

### Area utilities

- `GET /api/areas/search?q=...`
  - Uses ScanSan area search to resolve outward codes / area codes.

- `GET /api/areas/{area_code}/summary`
  - Calls ScanSan “area summary”.

- `POST /api/areas/compare`
  - Compares 2–3 areas and returns A2UI messages for the comparison tab.

## ScanSan API (External)

Client wrapper: `backend/app/scansan_client.py`

The OpenAPI (`api-1.json`) shows the endpoints this project uses or may use.

### Endpoints actively used by the app

- `GET /v1/area_codes/search`
  - Used for: resolving user-entered locations (e.g. `NW1`, `E14`) into a district/area code.

- `GET /v1/area_codes/{area_code}/summary`
  - Used for: “location comparison” summaries and market overview stats.

- `GET /v1/area_codes/{area_code}/rent/listings`
- `GET /v1/area_codes/{area_code}/sale/listings`
  - Used for: Property Finder tab (list + optional map), and comparison listings counts/ranges.

- `GET /v1/district/{area_code_district}/growth`
  - Used for: Growth charts in Market Data tab.

- `GET /v1/district/{area_code_district}/rent/demand`
- `GET /v1/district/{area_code_district}/sale/demand`
  - Used for: rent demand / sales demand visuals in Market Data tab.

- `GET /v1/postcode/{area_code_postal}/valuations/current`
- `GET /v1/postcode/{area_code_postal}/valuations/historical`
  - Used for: current vs historical valuations cards/charts (postcode-level).

- `GET /v1/postcode/{area_code_postal}/sale/history`
  - Used for: sale history table + export.

- `GET /v1/postcode/{area_code_postal}/amenities`
  - Used for: Property Finder “nearby amenities” (when enabled).

- `GET /v1/postcode/{area_code_postal}/energy/performance`
  - Used for: Sustainability / embodied carbon feature.

### Optional / nice-to-have endpoints (in OpenAPI)

These are present in `api-1.json` and are good candidates for future features:

- `GET /v1/postcode/{area_code_postal}/census` (demographics)
- `GET /v1/postcode/{area_code_postal}/regeneration` (area investment/regeneration signals)
- `GET /v1/postcode/{area_code_postal}/lha` (Local Housing Allowance context)
- Crime:
  - `GET /v1/area_codes/{area_code}/crime/summary`
  - `GET /v1/area_codes/{area_code}/crime/detail`

