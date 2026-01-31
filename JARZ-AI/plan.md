# plan.md — Spatio-Temporal Rental Valuation (ScanSan + LangGraph + A2UI)

## Project brief
We are building a **Spatio-Temporal Rental Valuation** demo for the RealTech Hackathon track:
- Predict rental values by learning **temporal dependence** (past rent trends) and **spatial dependence** (nearby areas’ rents).
- Deliver outputs as:
  - **Rent prediction** + **confidence band (P10/P50/P90)** via quantile predictions
  - **Explainability** via SHAP (top drivers)
  - **Generative UI** rendered from structured JSON (A2UI pattern)

### Scope split (IMPORTANT)
- **Model training + model artifact** is built by: **Teammate (not this repo/agent)**
- **This repo builds**:
  1) **Backend**: FastAPI + LangGraph orchestration + data fetch + feature build + model inference integration
  2) **Frontend**: Next.js + A2UI-style generative components (map, timeline, drivers)
  3) **Integration contract** between agent and the model (placeholder stub until model is ready)

---

## High-level architecture
1. **Frontend (Next.js)** renders UI by consuming **A2UI JSON stream** from backend.
2. **Backend (FastAPI)** hosts:
   - LangGraph agent (state machine)
   - ScanSan client + optional OSM/GIS enrichment
   - Feature builder (spatio + temporal lags)
   - Model adapter:
     - placeholder model (stub) for dev
     - swap-in trained quantile model later
   - SHAP explainer (optional fallback if not available)

---

## Deliverables checklist (build order)

### 0) Repo setup
- [ ] Create project structure:
  - `backend/` (FastAPI + LangGraph)
  - `frontend/` (Next.js + A2UI renderer)
  - `shared/` (pydantic schemas, component contracts)
  - `docs/` (API notes, demo script)
- [ ] Add `.env.example` for keys/config (ScanSan base URL, token, cache toggles)

---

## 1) Shared contracts (schemas & interfaces)
> Goal: make model + agent + UI plug together cleanly.

### 1.1 Data contracts
- [ ] Define pydantic types (in `shared/schemas.py`):
  - `UserQuery`: `location_input`, `area_code`, `horizon_months`, `view_mode` (`single|compare`), `radius_km`, `k_neighbors`
  - `ModelFeatures`: dict-like structure (allow flexible features)
  - `PredictionResult`:
    - `p10`, `p50`, `p90` (rent)
    - `unit` (e.g., "GBP/month")
    - `timestamp` / `horizon_months`
    - `metadata` (model_version, feature_version)
  - `ExplanationResult`:
    - `drivers`: list of `{name, contribution, direction}`
    - `base_value` (optional)
  - `A2UIMessage`: `{type, component, props, id}`

### 1.2 Model adapter interface (CRITICAL)
- [ ] Create `backend/model_adapter.py` with an interface like:

  **Required function**
  - `predict_quantiles(features: ModelFeatures) -> PredictionResult`

  **Optional**
  - `predict_quantiles_batch(list[ModelFeatures]) -> list[PredictionResult]`

- [ ] Implement **placeholder model adapter**:
  - deterministic + seeded random outputs
  - returns plausible P10/P50/P90
  - used until teammate model is available

- [ ] Add swap-in mechanism:
  - `MODEL_PROVIDER=stub|local_pickle|http`
  - If `local_pickle`: load a saved model artifact (path from env)
  - If `http`: call teammate’s model service endpoint (URL from env)

**NOTE**: The coding agent should NOT implement full training. Only adapters + stubs + integration hooks.

---

## 2) ScanSan API client + caching
> Goal: get features from sponsor API at runtime (and/or cache for reliability).

### 2.1 Client
- [ ] Create `backend/scansan_client.py` with:
  - auth header support
  - retries + timeouts
  - rate limit friendly backoff
- [ ] Implement endpoints (minimum):
  - `area_codes_search(query: str)`
  - `area_summary(area_code: str)`
  - `rent_listings(area_code: str, filters...)`
  - `district_rent_demand(area_code_district: str, period: str|None)`
  - `district_growth(area_code_district: str)`

### 2.2 Caching layer
- [ ] Add `backend/cache.py`:
  - in-memory LRU (fast)
  - optional disk cache (json) for demo stability
- [ ] Cache keys include: endpoint + params
- [ ] TTL per resource:
  - search: long TTL
  - demand/listings: shorter TTL (or fixed for hackathon)

---

## 3) Feature engineering (spatio + temporal)
> Goal: build the “dependence” features the model needs.

### 3.1 Location normalization
- [ ] `resolve_location(location_input)`:
  - uses ScanSan search
  - returns standardized `area_code` + `area_code_district` + centroid lat/lon if available
- [ ] If ScanSan doesn’t return lat/lon, store a fallback geometry mapping (static demo file).

### 3.2 Temporal features
- [ ] Build time-lag features from:
  - district growth series (if available)
  - cached historical snapshots (if available)
- [ ] Features examples:
  - `rent_growth_mom`, `rent_growth_yoy`
  - `demand_index_t`, `demand_index_t-1` (if period series available)
  - `month`, `quarter`

### 3.3 Spatial neighbor graph
- [ ] Implement `neighbors.py`:
  - build neighbor list for a district based on:
    - `k_neighbors` using centroid distance (preferred)
    - OR radius-km filtering
- [ ] Compute spatial lag features:
  - neighbor average demand, neighbor average growth, neighbor rent proxies if available

### 3.4 Final feature assembly
- [ ] `build_features(query: UserQuery) -> ModelFeatures`:
  - merges:
    - area summary stats
    - demand stats
    - growth stats
    - spatial lag aggregates
    - time metadata

**NOTE**: This feature builder is the core of “spatio-temporal dependence” in the demo.

---

## 4) Explainability (SHAP) integration
> Goal: “why did the model predict this?”

### 4.1 SHAP strategy
- [ ] Implement `backend/explain.py` with:
  - `explain_prediction(model, features) -> ExplanationResult`
- [ ] If model is `stub`:
  - return heuristic drivers (based on feature weights)
- [ ] If model is real tree model:
  - load SHAP explainer once at startup (if feasible)
  - compute SHAP values per request (single row)
  - return top N features (e.g., 8)

**Important**: SHAP is computed **on the fly at runtime** from the trained model + current features (not “trained separately”).

---

## 5) LangGraph agent orchestration (backend brain)
> Goal: controlled pipeline that outputs A2UI messages.

### 5.1 Agent state
- [ ] Define state:
  - query params
  - resolved location
  - raw fetched data
  - features
  - prediction
  - explanation
  - ui_messages

### 5.2 Agent nodes (must implement)
- [ ] `ResolveLocationNode`
- [ ] `FetchDataNode` (ScanSan calls + caching)
- [ ] `BuildFeaturesNode`
- [ ] `PredictNode` (calls model adapter)
- [ ] `ExplainNode` (SHAP / heuristic)
- [ ] `RenderA2UINode` (build component messages)
- [ ] `CompareFlowNode` (if view_mode=compare)

### 5.3 Agent entrypoints
- [ ] REST endpoint: `POST /api/query`
  - returns full response JSON
- [ ] Streaming endpoint (recommended): `POST /api/stream`
  - Server-Sent Events (SSE) streaming A2UI messages
  - each message is an `A2UIMessage`

---

## 6) A2UI Generative UI frontend (Next.js)
> Goal: render structured component messages from the agent.

### 6.1 A2UI renderer
- [ ] Build `frontend/components/A2UIRenderer.tsx`:
  - accepts a list/stream of messages
  - renders by `component` name mapping:
    - `RentForecastChart`
    - `NeighbourHeatmapMap`
    - `DriversBar`
    - `CompsTable`
    - `SummaryCard`
    - `WhatIfControls`

### 6.2 UI components (minimum)
- [ ] `SummaryCard`
  - shows P50 rent + band + key takeaway text
- [ ] `RentForecastChart`
  - line for P50 + shaded band for P10–P90 over horizon
  - include historical context if available
- [ ] `NeighbourHeatmapMap`
  - simple choropleth/heatmap:
    - selected district highlighted
    - neighbors highlighted
- [ ] `DriversBar`
  - horizontal bar chart of top SHAP contributors (+/-)
- [ ] `WhatIfControls`
  - horizon slider (1/3/6/12 months)
  - neighbor radius/k slider
  - compare mode toggle

### 6.3 Data flow (frontend)
- [ ] `useAgentStream()` hook:
  - calls `/api/stream`
  - appends streamed A2UI messages
  - re-renders incremental UI

---

## 7) Example user flows (for demo + agent behavior)
### Flow A: Single area forecast
1. User enters: “NW1”
2. Backend resolves to district via ScanSan search.
3. Agent fetches:
   - summary, demand, growth, listings stats
4. Agent builds features (lags + neighbor aggregates).
5. Agent predicts P10/P50/P90 rent for 6 months.
6. Agent computes SHAP drivers.
7. Frontend renders:
   - SummaryCard
   - RentForecastChart (band)
   - NeighbourHeatmapMap (neighbors)
   - DriversBar

### Flow B: Compare two districts
1. User enters: “NW1 vs E14”
2. Agent runs pipeline twice (or batch).
3. UI renders:
   - Comparison table
   - Two timelines
   - “why difference” drivers (top features that diverge)

### Flow C: What-if (spatio/temporal sensitivity)
1. User changes horizon 6 → 12 months
2. Agent rebuilds temporal features and re-predicts
3. UI updates chart + summary

---

## 8) ScanSan API reference (quick)
> Implement these in `scansan_client.py` (exact params may vary; keep flexible).

- `GET /v1/area_codes/search?search_term=...`
  - normalize user input to area codes
- `GET /v1/area_codes/{area_code}/summary`
  - counts + ranges + context stats
- `GET /v1/area_codes/{area_code}/rent/listings?...`
  - rental comps distribution
- `GET /v1/district/{area_code_district}/rent/demand?period=YYYY-MM`
  - demand index (time-aware if available)
- `GET /v1/district/{area_code_district}/growth`
  - growth series (MoM/YoY)

**Note**: Treat ScanSan as runtime feature source + location resolver.
Training can also use it, but this repo focuses on runtime + orchestration.

---

## 9) Integration notes for teammate model (handoff contract)
Teammate provides either:
- A local file: `model.pkl` (or similar) + feature spec
OR
- A service endpoint: `POST /predict` accepting `ModelFeatures`

**Expected output (must include):**
- `p10`, `p50`, `p90` rents (GBP/month)
- optional: model version, training window, feature list

**If teammate only provides P50:**
- fallback: conformal/quantile wrapper later, but prefer direct quantiles.

---

## 10) Acceptance criteria
- [ ] User can enter a district/postcode and get:
  - predicted rent P50
  - confidence band P10–P90
  - explanation drivers
  - map + timeline rendered from A2UI messages
- [ ] Compare mode works for two locations
- [ ] System still functions on stub model (for dev)
- [ ] Swap-in real model is one config change

---

## 11) Demo script (30–60 seconds)
- “We model rent as a spatio-temporal process: past trends + neighbor effects.”
- Show a district:
  - timeline with P10–P90 band
  - map highlighting neighbor graph
  - SHAP drivers explaining which factors matter
- Toggle horizon and show updated prediction live.
