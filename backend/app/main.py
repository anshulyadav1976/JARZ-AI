"""FastAPI application with SSE streaming for A2UI and chat."""
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from .schemas import UserQuery, QueryRequest, QueryResponse
from .agent.graph import run_agent, stream_agent, run_chat_agent, stream_chat_agent
from .agent.state import ChatMessage
from .scansan_client import get_scansan_client
from .llm_client import get_llm_client


# Request models for chat API
class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    message: str
    history: Optional[list[dict]] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("Starting JARZ Rental Valuation API...")
    yield
    # Shutdown
    scansan_client = get_scansan_client()
    await scansan_client.close()
    llm_client = get_llm_client()
    await llm_client.close()
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


# =============================================================================
# Chat API Endpoints
# =============================================================================

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest) -> dict:
    """
    Chat endpoint - run conversational agent and return response.
    
    This runs the chat agent which can call tools and respond to the user.
    Returns the full response including any A2UI messages.
    """
    try:
        # Convert history to proper format
        history: list[ChatMessage] = []
        if request.history:
            for msg in request.history:
                history.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content"),
                    "tool_calls": msg.get("tool_calls"),
                    "tool_call_id": msg.get("tool_call_id"),
                    "name": msg.get("name"),
                })
        
        # Run chat agent
        final_state = await run_chat_agent(request.message, history)
        
        # Check for errors
        if final_state.get("error"):
            raise HTTPException(status_code=400, detail=final_state["error"])
        
        # Get the last assistant message
        messages = final_state.get("messages", [])
        assistant_response = None
        for msg in reversed(messages):
            if msg.get("role") == "assistant" and msg.get("content"):
                assistant_response = msg["content"]
                break
        
        return {
            "success": True,
            "response": assistant_response,
            "a2ui_messages": final_state.get("a2ui_messages", []),
            "messages": messages,  # Full conversation history
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def generate_chat_sse_events(
    message: str,
    history: list[ChatMessage] = None,
) -> AsyncGenerator[dict, None]:
    """Generate SSE events from chat agent execution."""
    try:
        async for event in stream_chat_agent(message, history):
            event_type = event.get("type", "unknown")
            
            if event_type == "node":
                yield {
                    "event": "status",
                    "data": json.dumps({
                        "node": event.get("node"),
                        "status": event.get("status"),
                    }),
                }
            
            elif event_type == "text":
                yield {
                    "event": "text",
                    "data": json.dumps({
                        "content": event.get("content", ""),
                    }),
                }
            
            elif event_type == "tool_start":
                yield {
                    "event": "tool_start",
                    "data": json.dumps({
                        "tool": event.get("tool"),
                        "arguments": event.get("arguments"),
                    }),
                }
            
            elif event_type == "tool_end":
                yield {
                    "event": "tool_end",
                    "data": json.dumps({
                        "tool": event.get("tool"),
                        "success": event.get("success"),
                    }),
                }
            
            elif event_type == "a2ui":
                # Stream each A2UI message individually
                for a2ui_msg in event.get("messages", []):
                    yield {
                        "event": "a2ui",
                        "data": json.dumps(a2ui_msg),
                    }
            
            elif event_type == "error":
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "error": event.get("error"),
                    }),
                }
            
            elif event_type == "complete":
                # Stream any remaining A2UI messages
                for a2ui_msg in event.get("a2ui_messages", []):
                    yield {
                        "event": "a2ui",
                        "data": json.dumps(a2ui_msg),
                    }
                
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "status": "complete",
                    }),
                }
    
    except Exception as e:
        yield {
            "event": "error",
            "data": json.dumps({"error": str(e)}),
        }


@app.post("/api/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Streaming chat endpoint - returns SSE stream of text chunks and A2UI messages.
    
    Events:
    - status: Agent status updates (node, status)
    - text: Text content chunks from assistant
    - tool_start: Tool execution started
    - tool_end: Tool execution completed
    - a2ui: A2UI component message
    - error: Error occurred
    - complete: Processing complete
    """
    # Convert history
    history: list[ChatMessage] = []
    if request.history:
        for msg in request.history:
            history.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content"),
                "tool_calls": msg.get("tool_calls"),
                "tool_call_id": msg.get("tool_call_id"),
                "name": msg.get("name"),
            })
    
    return EventSourceResponse(
        generate_chat_sse_events(request.message, history),
        media_type="text/event-stream",
    )


# =============================================================================
# Property Listings API Endpoints
# =============================================================================

@app.post("/api/properties/listings")
async def get_property_listings(request: dict):
    """
    Get property listings for an area.
    
    Request body:
    - area_code: Area code (e.g., "NW1")
    - listing_type: "rent" or "sale"
    - min_beds: Optional minimum bedrooms
    - max_beds: Optional maximum bedrooms
    - property_type: Optional property type filter
    """
    try:
        area_code = request.get("area_code")
        listing_type = request.get("listing_type", "rent")
        min_beds = request.get("min_beds")
        max_beds = request.get("max_beds")
        property_type = request.get("property_type")
        
        if not area_code:
            raise HTTPException(status_code=400, detail="area_code is required")
        
        scansan_client = get_scansan_client()
        
        if listing_type == "sale":
            data = await scansan_client.get_sale_listings(
                area_code=area_code,
                min_beds=min_beds,
                max_beds=max_beds,
                property_type=property_type,
            )
        else:
            data = await scansan_client.get_rent_listings(
                area_code=area_code,
                min_beds=min_beds,
                max_beds=max_beds,
                property_type=property_type,
            )
        
        return {
            "success": True,
            "area_code": area_code,
            "listing_type": listing_type,
            "data": data,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
