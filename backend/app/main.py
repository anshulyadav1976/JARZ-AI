"""FastAPI application with SSE streaming for A2UI and chat."""
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from pydantic import BaseModel

import csv
import io

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sse_starlette.sse import EventSourceResponse

from .schemas import UserQuery, QueryRequest, QueryResponse
from .agent.graph import run_agent, stream_agent, run_chat_agent, stream_chat_agent
from .agent.state import ChatMessage
from .scansan_client import get_scansan_client
from . import db as chat_db
from .llm_client import get_llm_client
from .agent.tools import execute_compare_areas


# Request models for chat API
class UserProfile(BaseModel):
    """Optional user profile for personalisation (injected into system prompt)."""
    name: Optional[str] = None
    role: Optional[str] = None  # "investor" | "property_agent" | "individual"
    bio: Optional[str] = None
    interests: Optional[list[str]] = None  # e.g. sustainability, investment_returns, location_comparison
    preferences: Optional[str] = None  # free text: what they're looking for


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    message: str
    history: Optional[list[dict]] = None
    conversation_id: Optional[str] = None
    profile: Optional[UserProfile] = None


class CompareAreasRequest(BaseModel):
    """Request for area comparison endpoint."""
    areas: list[str]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("Starting JARZ Rental Valuation API...")
    chat_db.init_db()
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
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
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
# Amenities API Endpoint
# =============================================================================

@app.get("/api/postcode/{area_code_postal}/amenities")
async def get_amenities(area_code_postal: str):
    """
    Fetch nearest amenities for a given postcode or outward area code.

    Accepts either a full postcode (e.g., "NW1 0BH") or an outward code (e.g., "NW1").
    Returns a normalized list of amenities with type, name, and distance in miles.
    """
    try:
        client = get_scansan_client()
        data = await client.get_amenities(area_code_postal)
        # Normalize shape to a flat list for frontend
        amenities: list[dict] = []
        if data and "data" in data:
            raw = data["data"]
            # Some ScanSan responses use nested arrays; flatten cautiously
            if isinstance(raw, list):
                for group in raw:
                    if isinstance(group, list):
                        for item in group:
                            amenity_type = item.get("amenity_type") or item.get("type")
                            name = item.get("name") or item.get("amenity_name")
                            distance = item.get("distance_miles") or item.get("distance")
                            if amenity_type and name is not None:
                                amenities.append({
                                    "type": str(amenity_type),
                                    "name": str(name),
                                    "distance": float(distance) if distance is not None else None,
                                })
            else:
                # If data structure differs, attempt to map keys directly
                for item in raw:
                    amenity_type = item.get("amenity_type")
                    name = item.get("name")
                    distance = item.get("distance_miles")
                    if amenity_type and name is not None:
                        amenities.append({
                            "type": str(amenity_type),
                            "name": str(name),
                            "distance": float(distance) if distance is not None else None,
                        })

        return {"success": True, "area_code_postal": area_code_postal, "amenities": amenities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# District / Postcode Data (Growth, Demand, Valuations, Sale History)
# =============================================================================

@app.get("/api/district/{district}/growth")
async def get_district_growth(district: str):
    """Get month-on-month and year-on-year growth for district."""
    client = get_scansan_client()
    data = await client.get_district_growth(district.strip().upper())
    if data is None:
        return {"success": False, "district": district, "data": None}
    return {"success": True, "district": district, "data": data.get("data"), "area_code": data.get("area_code")}


@app.get("/api/district/{district}/rent/demand")
async def get_district_rent_demand(
    district: str,
    period: Optional[str] = None,
    additional_data: bool = False,
):
    """Get rental demand data for district."""
    client = get_scansan_client()
    data = await client.get_district_demand(
        district.strip().upper(),
        period=period,
        additional_data=additional_data,
    )
    if data is None:
        return {"success": False, "district": district, "data": None}
    return {
        "success": True,
        "district": district,
        "data": data.get("data"),
        "area_code": data.get("area_code"),
        "target_month": data.get("target_month"),
        "target_year": data.get("target_year"),
    }


@app.get("/api/district/{district}/sale/demand")
async def get_district_sale_demand(
    district: str,
    period: Optional[str] = None,
    additional_data: bool = False,
):
    """Get sales demand data for district."""
    client = get_scansan_client()
    data = await client.get_sale_demand(
        district.strip().upper(),
        period=period,
        additional_data=additional_data,
    )
    if data is None:
        return {"success": False, "district": district, "data": None}
    return {
        "success": True,
        "district": district,
        "data": data.get("data"),
        "area_code": data.get("area_code"),
        "target_month": data.get("target_month"),
        "target_year": data.get("target_year"),
    }


@app.get("/api/postcode/{postcode}/valuations/current")
async def get_postcode_valuations_current(postcode: str):
    """Get current valuations for each address in postcode."""
    client = get_scansan_client()
    data = await client.get_current_valuations(postcode.strip().replace(" ", "").upper())
    if data is None:
        return {"success": False, "postcode": postcode, "data": None}
    return {"success": True, "postcode": postcode, "data": data.get("data")}


@app.get("/api/postcode/{postcode}/valuations/historical")
async def get_postcode_valuations_historical(postcode: str):
    """Get historical valuations for each address in postcode."""
    client = get_scansan_client()
    data = await client.get_historical_valuations(postcode.strip().replace(" ", "").upper())
    if data is None:
        return {"success": False, "postcode": postcode, "data": None}
    return {"success": True, "postcode": postcode, "data": data.get("data")}


@app.get("/api/postcode/{postcode}/sale/history")
async def get_postcode_sale_history(postcode: str):
    """Get sale history for properties in postcode."""
    client = get_scansan_client()
    data = await client.get_sale_history(postcode.strip().replace(" ", "").upper())
    if data is None:
        return {"success": False, "postcode": postcode, "data": None}
    return {"success": True, "postcode": postcode, "data": data.get("data")}


@app.get("/api/postcode/{postcode}/sale/history/export")
async def export_postcode_sale_history(postcode: str):
    """Export sale history for postcode as CSV download."""
    client = get_scansan_client()
    data = await client.get_sale_history(postcode.strip().replace(" ", "").upper())
    if data is None or not data.get("data"):
        raise HTTPException(status_code=404, detail="No sale history found for this postcode")

    rows = []
    for prop in data["data"]:
        addr = prop.get("property_address", "")
        uprn = prop.get("uprn", "")
        ptype = prop.get("property_type", "")
        for tx in prop.get("transactions", []):
            rows.append({
                "property_address": addr,
                "uprn": uprn,
                "property_type": ptype,
                "sold_date": tx.get("sold_date", ""),
                "sold_price": tx.get("sold_price", ""),
                "property_tenure": tx.get("property_tenure", ""),
                "price_diff_amount": tx.get("price_diff_amount", ""),
                "price_diff_percentage": tx.get("price_diff_percentage", ""),
            })

    if not rows:
        raise HTTPException(status_code=404, detail="No transactions found for this postcode")

    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    csv_str = out.getvalue()

    safe_postcode = postcode.strip().replace(" ", "").upper()
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="sale_history_{safe_postcode}.csv"'},
    )


@app.post("/api/areas/compare")
async def compare_areas_endpoint(request: CompareAreasRequest):
    """
    Compare 2-3 areas using ScanSan area summary.

    This endpoint is intended for the frontend "Location Comparison" tab.
    It returns a2ui_messages so the UI can render charts without involving the LLM.
    """
    result = await execute_compare_areas(areas=request.areas)
    return {
        "success": bool(result.get("success")),
        "areas": result.get("areas", []),
        "winners": result.get("winners", {}),
        "a2ui_messages": result.get("a2ui_messages", []),
        "summary": result.get("summary"),
    }


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


def _profile_to_dict(profile: Optional[UserProfile]) -> Optional[dict]:
    """Convert UserProfile to dict for agent state."""
    if not profile:
        return None
    d = profile.model_dump(exclude_none=True)
    return d if d else None


async def generate_chat_sse_events(
    message: str,
    history: list[ChatMessage] = None,
    conversation_id: Optional[str] = None,
    profile: Optional[dict] = None,
) -> AsyncGenerator[dict, None]:
    """Generate SSE events from chat agent execution. Persists to DB and emits conversation_id on complete."""
    history = history or []
    # Resolve or create conversation and persist user message
    cid = conversation_id
    if not cid:
        title = (message[:200].strip() or "New chat") if message else "New chat"
        cid = chat_db.create_conversation(title=title)
        chat_db.add_message(cid, "user", message)
    else:
        chat_db.add_message(cid, "user", message)
        chat_db.update_conversation_updated_at(cid)

    accumulated_text: list[str] = []
    a2ui_for_save: list = []

    try:
        async for event in stream_chat_agent(message, history, profile=profile):
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
                content = event.get("content", "")
                print(f"[SSE] Received text event, content length: {len(content)}, preview: {content[:100]}")
                yield {
                    "event": "text",
                    "data": json.dumps({
                        "content": content,
                    }),
                }
                print(f"[SSE] Yielded text event")

            
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
            
            elif event_type == "market_data_request":
                yield {
                    "event": "market_data_request",
                    "data": json.dumps({
                        "district": event.get("district"),
                        "postcode": event.get("postcode"),
                    }),
                }
            
            elif event_type == "a2ui":
                # Stream each A2UI message individually
                messages_list = event.get("messages", [])
                print(f"\n[SSE] Streaming {len(messages_list)} A2UI messages")
                for i, a2ui_msg in enumerate(messages_list):
                    msg_keys = list(a2ui_msg.keys())
                    print(f"[SSE]   Message {i}: {msg_keys}")
                    serialized = json.dumps(a2ui_msg)
                    print(f"[SSE]   Serialized length: {len(serialized)} chars")
                    yield {
                        "event": "a2ui",
                        "data": serialized,
                    }
            
            elif event_type == "error":
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "error": event.get("error"),
                    }),
                }
            
            elif event_type == "complete":
                a2ui_for_save = event.get("a2ui_messages", [])
                # Stream any remaining A2UI messages
                for a2ui_msg in a2ui_for_save:
                    yield {
                        "event": "a2ui",
                        "data": json.dumps(a2ui_msg),
                    }
                # Persist assistant message (text + A2UI snapshot for replay)
                full_text = "".join(accumulated_text)
                chat_db.add_message(cid, "assistant", full_text, a2ui_snapshot=a2ui_for_save)
                yield {
                    "event": "complete",
                    "data": json.dumps({
                        "status": "complete",
                        "conversation_id": cid,
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
    Persists messages to SQLite; optional conversation_id continues an existing chat.
    Complete event includes conversation_id for new or existing conversations.
    
    Events:
    - status: Agent status updates (node, status)
    - text: Text content chunks from assistant
    - tool_start: Tool execution started
    - tool_end: Tool execution completed
    - a2ui: A2UI component message
    - error: Error occurred
    - complete: Processing complete (includes conversation_id)
    """
    history: list[ChatMessage] = []
    if request.conversation_id:
        conv = chat_db.get_conversation_with_messages(request.conversation_id)
        if conv and conv.get("messages"):
            for msg in conv["messages"]:
                if msg["role"] in ("user", "assistant", "system") and msg.get("content") is not None:
                    history.append({
                        "role": msg["role"],
                        "content": msg["content"],
                    })
    if not history and request.history:
        for msg in request.history:
            history.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content"),
                "tool_calls": msg.get("tool_calls"),
                "tool_call_id": msg.get("tool_call_id"),
                "name": msg.get("name"),
            })
    
    profile_dict = _profile_to_dict(request.profile)
    return EventSourceResponse(
        generate_chat_sse_events(request.message, history, request.conversation_id, profile=profile_dict),
        media_type="text/event-stream",
    )


# =============================================================================
# Conversation history API
# =============================================================================

@app.get("/api/conversations")
async def list_conversations(limit: int = 50):
    """List saved conversations, most recent first."""
    return chat_db.get_conversations(limit=limit)


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get one conversation with all messages (for loading chat history)."""
    conv = chat_db.get_conversation_with_messages(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


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


@app.get("/api/heatmap/areas")
async def get_heatmap_data(
    listing_type: str = "rent",
    bounds: Optional[str] = None,
):
    """
    Get heatmap data for London areas.
    
    Query params:
    - listing_type: "rent" or "sale" (default: rent)
    - bounds: Optional bounding box as "minLat,minLng,maxLat,maxLng"
    
    Returns aggregated price data for area codes with coordinates.
    """
    try:
        # Common London area codes (outward codes)
        # These are the main London postcodes we'll fetch data for
        london_areas = [
            # Central London
            "EC1", "EC2", "EC3", "EC4", "WC1", "WC2",
            "E1", "E2", "E3", "E8", "E9", "E14", "E15", "E16", "E20",
            "N1", "N4", "N5", "N7", "N16", "N19",
            "NW1", "NW3", "NW5", "NW6", "NW8",
            "SE1", "SE5", "SE8", "SE10", "SE11", "SE15", "SE16", "SE17",
            "SW1", "SW3", "SW5", "SW6", "SW7", "SW8", "SW9", "SW10", "SW11",
            "W1", "W2", "W6", "W8", "W9", "W10", "W11", "W12", "W14",
            # Outer London samples
            "BR1", "CR0", "DA14", "E4", "E10", "E11", "E12", "E13", "E17", "E18",
            "EN1", "HA0", "HA8", "IG1", "KT1", "N2", "N3", "N6", "N8", "N10",
            "N11", "N12", "N13", "N14", "N15", "N17", "N18", "N20", "N22",
            "NW2", "NW4", "NW7", "NW9", "NW10", "NW11",
            "RM1", "SE2", "SE3", "SE4", "SE6", "SE7", "SE9", "SE12", "SE13", "SE14", "SE18", "SE19", "SE20",
            "SM1", "SW2", "SW4", "SW12", "SW13", "SW15", "SW16", "SW17", "SW18", "SW19", "SW20",
            "TW1", "UB1", "W3", "W4", "W5", "W7", "W13",
        ]
        
        scansan_client = get_scansan_client()
        heatmap_data = []
        
        # Approximate coordinates for London postcodes (simplified mapping)
        # In a real implementation, you'd get these from a geocoding service
        area_coords = {
            # Central postcodes
            "EC1": (51.5200, -0.1050), "EC2": (51.5175, -0.0860), "EC3": (51.5130, -0.0820), "EC4": (51.5155, -0.1030),
            "WC1": (51.5240, -0.1280), "WC2": (51.5125, -0.1210),
            "E1": (51.5180, -0.0550), "E2": (51.5310, -0.0590), "E3": (51.5330, -0.0280), "E8": (51.5450, -0.0560), 
            "E9": (51.5550, -0.0490), "E14": (51.5050, -0.0200), "E15": (51.5420, -0.0050), "E16": (51.5100, 0.0240), "E20": (51.5450, -0.0100),
            "N1": (51.5400, -0.1050), "N4": (51.5650, -0.1000), "N5": (51.5580, -0.1050), "N7": (51.5550, -0.1180), "N16": (51.5600, -0.0750), "N19": (51.5650, -0.1310),
            "NW1": (51.5350, -0.1450), "NW3": (51.5550, -0.1680), "NW5": (51.5550, -0.1430), "NW6": (51.5500, -0.1900), "NW8": (51.5350, -0.1750),
            "SE1": (51.5020, -0.0950), "SE5": (51.4820, -0.0880), "SE8": (51.4870, -0.0280), "SE10": (51.4850, 0.0050), "SE11": (51.4930, -0.1150),
            "SE15": (51.4750, -0.0630), "SE16": (51.4950, -0.0550), "SE17": (51.4900, -0.0950),
            "SW1": (51.4975, -0.1357), "SW3": (51.4930, -0.1650), "SW5": (51.4920, -0.1900), "SW6": (51.4820, -0.1950), "SW7": (51.4950, -0.1750),
            "SW8": (51.4820, -0.1280), "SW9": (51.4680, -0.1180), "SW10": (51.4850, -0.1850), "SW11": (51.4650, -0.1650),
            "W1": (51.5140, -0.1480), "W2": (51.5150, -0.1780), "W6": (51.4950, -0.2280), "W8": (51.5030, -0.1930), 
            "W9": (51.5230, -0.1850), "W10": (51.5250, -0.2100), "W11": (51.5150, -0.2050), "W12": (51.5100, -0.2320), "W14": (51.4950, -0.2100),
            # Outer areas (approximate)
            "BR1": (51.4050, 0.0130), "CR0": (51.3720, -0.0980), "DA14": (51.4280, 0.1280), "E4": (51.6150, -0.0080), "E10": (51.5650, -0.0130),
            "E11": (51.5580, 0.0050), "E12": (51.5480, 0.0430), "E13": (51.5200, 0.0450), "E17": (51.5880, -0.0180), "E18": (51.5950, 0.0280),
            "EN1": (51.6520, -0.0820), "HA0": (51.5580, -0.2950), "HA8": (51.6150, -0.2780), "IG1": (51.5580, 0.0780), "KT1": (51.4100, -0.3050),
            "N2": (51.5800, -0.1480), "N3": (51.6050, -0.1750), "N6": (51.5680, -0.1430), "N8": (51.5850, -0.1180), "N10": (51.5980, -0.1480),
            "N11": (51.6120, -0.1050), "N12": (51.6180, -0.1480), "N13": (51.6150, -0.0980), "N14": (51.6380, -0.1180), "N15": (51.5880, -0.0780),
            "N17": (51.6020, -0.0680), "N18": (51.6180, -0.0580), "N20": (51.6280, -0.1650), "N22": (51.6050, -0.1080),
            "NW2": (51.5650, -0.2150), "NW4": (51.5850, -0.2280), "NW7": (51.6050, -0.2350), "NW9": (51.6080, -0.2650), 
            "NW10": (51.5450, -0.2450), "NW11": (51.5750, -0.1980),
            "RM1": (51.5780, 0.1850), "SE2": (51.4880, 0.0950), "SE3": (51.4650, 0.0150), "SE4": (51.4620, -0.0280), "SE6": (51.4480, -0.0180),
            "SE7": (51.4950, 0.0450), "SE9": (51.4450, 0.0480), "SE12": (51.4450, -0.0050), "SE13": (51.4580, -0.0180), "SE14": (51.4750, -0.0480),
            "SE18": (51.4950, 0.0880), "SE19": (51.4250, -0.0850), "SE20": (51.4120, -0.0550),
            "SM1": (51.3980, -0.1950), "SW2": (51.4550, -0.1250), "SW4": (51.4650, -0.1380), "SW12": (51.4550, -0.1650), "SW13": (51.4650, -0.2580),
            "SW15": (51.4580, -0.2250), "SW16": (51.4280, -0.1250), "SW17": (51.4280, -0.1680), "SW18": (51.4550, -0.1880), 
            "SW19": (51.4180, -0.1950), "SW20": (51.4080, -0.1950),
            "TW1": (51.4480, -0.3280), "UB1": (51.5180, -0.3480), "W3": (51.5180, -0.2680), "W4": (51.4950, -0.2580), 
            "W5": (51.5150, -0.3080), "W7": (51.5080, -0.3380), "W13": (51.5150, -0.3350),
        }
        
        # Fetch summary data for each area
        for area in london_areas:
            try:
                summary = await scansan_client.get_area_summary(area)
                
                if summary and "data" in summary:
                    data_list = summary["data"]
                    
                    # ScanSan returns data as a list, get first element
                    if isinstance(data_list, list) and len(data_list) > 0:
                        data = data_list[0]
                    else:
                        continue
                    
                    # Get coordinates
                    coords = area_coords.get(area, (51.5074, -0.1278))  # Default to London center
                    
                    # Extract price data based on listing type
                    if listing_type == "rent":
                        # Get rent data
                        rent_range = data.get("current_rent_listings_pcm_range")
                        listing_count = data.get("current_rent_listings", 0)
                        if rent_range and len(rent_range) == 2:
                            min_price = rent_range[0]
                            max_price = rent_range[1]
                            median_price = (min_price + max_price) / 2
                        else:
                            min_price = None
                            max_price = None
                            median_price = None
                    else:
                        # Get sale data
                        sale_range = data.get("current_sale_listings_price_range")
                        listing_count = data.get("current_sale_listings", 0)
                        if sale_range and len(sale_range) == 2:
                            min_price = sale_range[0]
                            max_price = sale_range[1]
                            median_price = (min_price + max_price) / 2
                        else:
                            min_price = None
                            max_price = None
                            median_price = None
                    
                    # Use median as the primary price
                    price = median_price
                    
                    if price:
                        heatmap_data.append({
                            "area_code": area,
                            "lat": coords[0],
                            "lng": coords[1],
                            "price": price,
                            "min_price": min_price,
                            "max_price": max_price,
                            "median_price": median_price,
                            "listing_count": listing_count,
                        })
            except Exception as e:
                print(f"[HEATMAP] Error fetching data for {area}: {e}")
                continue
        
        return {
            "success": True,
            "listing_type": listing_type,
            "count": len(heatmap_data),
            "data": heatmap_data,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/heatmap/crime")
async def get_crime_heatmap_data(bounds: Optional[str] = None):
    """
    Get crime heatmap data for London areas.
    
    Returns aggregated crime data for area codes with coordinates.
    """
    try:
        # Same London area codes
        london_areas = [
            # Central London
            "EC1", "EC2", "EC3", "EC4", "WC1", "WC2",
            "E1", "E2", "E3", "E8", "E9", "E14", "E15", "E16", "E20",
            "N1", "N4", "N5", "N7", "N16", "N19",
            "NW1", "NW3", "NW5", "NW6", "NW8",
            "SE1", "SE5", "SE8", "SE10", "SE11", "SE15", "SE16", "SE17",
            "SW1", "SW3", "SW5", "SW6", "SW7", "SW8", "SW9", "SW10", "SW11",
            "W1", "W2", "W6", "W8", "W9", "W10", "W11", "W12", "W14",
            # Outer London samples
            "BR1", "CR0", "DA14", "E4", "E10", "E11", "E12", "E13", "E17", "E18",
            "EN1", "HA0", "HA8", "IG1", "KT1", "N2", "N3", "N6", "N8", "N10",
            "N11", "N12", "N13", "N14", "N15", "N17", "N18", "N20", "N22",
            "NW2", "NW4", "NW7", "NW9", "NW10", "NW11",
            "RM1", "SE2", "SE3", "SE4", "SE6", "SE7", "SE9", "SE12", "SE13", "SE14", "SE18", "SE19", "SE20",
            "SM1", "SW2", "SW4", "SW12", "SW13", "SW15", "SW16", "SW17", "SW18", "SW19", "SW20",
            "TW1", "UB1", "W3", "W4", "W5", "W7", "W13",
        ]
        
        scansan_client = get_scansan_client()
        heatmap_data = []
        
        # Same coordinate mapping as price heatmap
        area_coords = {
            # Central postcodes
            "EC1": (51.5200, -0.1050), "EC2": (51.5175, -0.0860), "EC3": (51.5130, -0.0820), "EC4": (51.5155, -0.1030),
            "WC1": (51.5240, -0.1280), "WC2": (51.5125, -0.1210),
            "E1": (51.5180, -0.0550), "E2": (51.5310, -0.0590), "E3": (51.5330, -0.0280), "E8": (51.5450, -0.0560), 
            "E9": (51.5550, -0.0490), "E14": (51.5050, -0.0200), "E15": (51.5420, -0.0050), "E16": (51.5100, 0.0240), "E20": (51.5450, -0.0100),
            "N1": (51.5400, -0.1050), "N4": (51.5650, -0.1000), "N5": (51.5580, -0.1050), "N7": (51.5550, -0.1180), "N16": (51.5600, -0.0750), "N19": (51.5650, -0.1310),
            "NW1": (51.5350, -0.1450), "NW3": (51.5550, -0.1680), "NW5": (51.5550, -0.1430), "NW6": (51.5500, -0.1900), "NW8": (51.5350, -0.1750),
            "SE1": (51.5020, -0.0950), "SE5": (51.4820, -0.0880), "SE8": (51.4870, -0.0280), "SE10": (51.4850, 0.0050), "SE11": (51.4930, -0.1150),
            "SE15": (51.4750, -0.0630), "SE16": (51.4950, -0.0550), "SE17": (51.4900, -0.0950),
            "SW1": (51.4975, -0.1405), "SW3": (51.4925, -0.1635), "SW5": (51.4925, -0.1935), "SW6": (51.4825, -0.1935), "SW7": (51.4975, -0.1735),
            "SW8": (51.4825, -0.1235), "SW9": (51.4675, -0.1135), "SW10": (51.4875, -0.1835), "SW11": (51.4675, -0.1635),
            "W1": (51.5175, -0.1435), "W2": (51.5175, -0.1735), "W6": (51.4975, -0.2235), "W8": (51.5075, -0.1935), 
            "W9": (51.5275, -0.1835), "W10": (51.5275, -0.2135), "W11": (51.5175, -0.2035), "W12": (51.5175, -0.2335), "W14": (51.4975, -0.2135),
            # Outer areas
            "BR1": (51.4050, 0.0150), "CR0": (51.3750, -0.1000), "DA14": (51.4450, 0.1350), "E4": (51.6050, -0.0150), "E10": (51.5650, -0.0150),
            "E11": (51.5750, 0.0050), "E12": (51.5550, 0.0450), "E13": (51.5250, 0.0350), "E17": (51.5850, -0.0250), "E18": (51.5950, 0.0250),
            "EN1": (51.6550, -0.0550), "HA0": (51.5650, -0.3250), "HA8": (51.6050, -0.2850), "IG1": (51.5650, 0.0850), "KT1": (51.4150, -0.3050),
            "N2": (51.5850, -0.1450), "N3": (51.5950, -0.1650), "N6": (51.5650, -0.1450), "N8": (51.5850, -0.1150), "N10": (51.6050, -0.1450),
            "N11": (51.6150, -0.1050), "N12": (51.6150, -0.1550), "N13": (51.6250, -0.1050), "N14": (51.6350, -0.1350), "N15": (51.5950, -0.0850),
            "N17": (51.6050, -0.0650), "N18": (51.6150, -0.0550), "N20": (51.6250, -0.1750), "N22": (51.6050, -0.1250),
            "NW2": (51.5650, -0.2150), "NW4": (51.6050, -0.2250), "NW7": (51.6250, -0.2150), "NW9": (51.6150, -0.2550), "NW10": (51.5450, -0.2450), "NW11": (51.5850, -0.1950),
            "RM1": (51.5750, 0.1750), "SE2": (51.4850, 0.1150), "SE3": (51.4650, 0.0150), "SE4": (51.4650, -0.0350), "SE6": (51.4450, -0.0050),
            "SE7": (51.4950, 0.0650), "SE9": (51.4450, 0.0550), "SE12": (51.4550, -0.0150), "SE13": (51.4550, -0.0250), "SE14": (51.4750, -0.0550),
            "SE18": (51.4950, 0.0950), "SE19": (51.4250, -0.0850), "SE20": (51.4150, -0.0650),
            "SM1": (51.4050, -0.1950), "SW2": (51.4575, -0.1235), "SW4": (51.4675, -0.1435), "SW12": (51.4575, -0.1635), "SW13": (51.4675, -0.2335),
            "SW15": (51.4575, -0.2135), "SW16": (51.4275, -0.1335), "SW17": (51.4275, -0.1635), "SW18": (51.4575, -0.1935), "SW19": (51.4275, -0.1935), "SW20": (51.4175, -0.1935),
            "TW1": (51.4475, -0.3350), "UB1": (51.5350, -0.3650), "W3": (51.5175, -0.2635), "W4": (51.4975, -0.2535), "W5": (51.5175, -0.3035),
            "W7": (51.5075, -0.3135), "W13": (51.5175, -0.3335),
        }
        
        # Fetch crime data for each area
        for area in london_areas:
            try:
                crime_summary = await scansan_client.get_crime_summary(area)
                
                if crime_summary:
                    # The response structure is:
                    # { "area_code": "...", "data": { "total_incidents": 1819, ... } }
                    data = crime_summary.get("data", {})
                    
                    # Get coordinates
                    coords = area_coords.get(area, (51.5074, -0.1278))
                    
                    # Extract crime metrics - API returns total_incidents, not total_crimes
                    total_incidents = data.get("total_incidents", 0)
                    
                    if total_incidents > 0:
                        heatmap_data.append({
                            "area_code": area,
                            "lat": coords[0],
                            "lng": coords[1],
                            "crime_count": total_incidents,
                            "crime_rate": None,  # Not provided by API
                        })
            except Exception as e:
                print(f"[HEATMAP] Error fetching crime data for {area}: {e}")
                continue
        
        return {
            "success": True,
            "count": len(heatmap_data),
            "data": heatmap_data,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
