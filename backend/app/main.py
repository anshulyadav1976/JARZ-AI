"""FastAPI application with SSE streaming for A2UI."""
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from .schemas import UserQuery, QueryRequest, QueryResponse
from .agent.graph import run_agent, stream_agent
from .scansan_client import get_scansan_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("Starting JARZ Rental Valuation API...")
    yield
    # Shutdown
    client = get_scansan_client()
    await client.close()
    print("Shutting down...")


app = FastAPI(
    title="JARZ Rental Valuation API",
    description="Spatio-Temporal Rental Valuation with A2UI streaming",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "JARZ Rental Valuation"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/query")
async def query_endpoint(request: QueryRequest) -> dict:
    """
    Full query endpoint - returns complete response.
    
    This runs the entire agent pipeline and returns the final result.
    """
    try:
        # Run agent
        final_state = await run_agent(request.query)
        
        # Check for errors
        if final_state.get("error"):
            raise HTTPException(status_code=400, detail=final_state["error"])
        
        # Build response
        return {
            "success": True,
            "location": final_state.get("resolved_location"),
            "prediction": final_state.get("prediction"),
            "explanation": final_state.get("explanation"),
            "neighbors": final_state.get("neighbors", []),
            "ui_messages": final_state.get("ui_messages", []),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def generate_sse_events(query: UserQuery) -> AsyncGenerator[dict, None]:
    """Generate SSE events from agent execution."""
    try:
        # Run the agent and get final state
        final_state = await run_agent(query)
        
        if final_state.get("error"):
            yield {
                "event": "error",
                "data": json.dumps({"error": final_state["error"]}),
            }
            return
        
        # Stream each UI message
        ui_messages = final_state.get("ui_messages", [])
        
        for i, message in enumerate(ui_messages):
            yield {
                "event": "message",
                "data": json.dumps(message),
                "id": str(i),
            }
        
        # Send completion event
        yield {
            "event": "complete",
            "data": json.dumps({
                "status": "complete",
                "message_count": len(ui_messages),
            }),
        }
    
    except Exception as e:
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)}),
        }


@app.post("/api/stream")
async def stream_endpoint(request: QueryRequest):
    """
    Streaming endpoint - returns SSE stream of A2UI messages.
    
    Each message is a JSONL line that the frontend can render progressively.
    """
    return EventSourceResponse(
        generate_sse_events(request.query),
        media_type="text/event-stream",
    )


# Additional utility endpoints

@app.get("/api/areas/search")
async def search_areas(q: str):
    """Search for area codes."""
    client = get_scansan_client()
    location = await client.search_area_codes(q)
    if location:
        return {"results": [location]}
    return {"results": []}


@app.get("/api/areas/{area_code}/summary")
async def get_area_summary(area_code: str):
    """Get summary for area code."""
    client = get_scansan_client()
    summary = await client.get_area_summary(area_code)
    return summary


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
