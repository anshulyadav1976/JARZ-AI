"""LangGraph agent nodes."""
from typing import Any
from .state import AgentState
from ..schemas import UserQuery, ResolvedLocation, Neighbor
from ..scansan_client import get_scansan_client
from ..feature_builder import build_features
from ..model_adapter import get_model_adapter
from ..explain import explain_prediction
from ..a2ui_builder import build_complete_ui


async def resolve_location_node(state: AgentState) -> dict[str, Any]:
    """
    Resolve user location input to standardized area code.
    """
    try:
        query = state["query"]
        client = get_scansan_client()
        
        location = await client.search_area_codes(query.location_input)
        
        if location is None:
            return {
                "error": f"Could not resolve location: {query.location_input}",
                "status": "error",
            }
        
        return {
            "resolved_location": location,
            "status": "location_resolved",
        }
    
    except Exception as e:
        return {
            "error": f"Location resolution failed: {str(e)}",
            "status": "error",
        }


async def fetch_data_node(state: AgentState) -> dict[str, Any]:
    """
    Fetch data from ScanSan API.
    """
    try:
        location = state.get("resolved_location")
        if not location:
            return {"error": "No resolved location", "status": "error"}
        
        client = get_scansan_client()
        
        # Fetch all data in parallel would be ideal, but for simplicity:
        summary = await client.get_area_summary(location.area_code)
        
        district = location.area_code_district or location.area_code
        demand = await client.get_district_demand(district)
        growth = await client.get_district_growth(district)
        
        raw_data = {
            "summary": summary,
            "demand": demand,
            "growth": growth,
        }
        
        return {
            "raw_data": raw_data,
            "status": "data_fetched",
        }
    
    except Exception as e:
        return {
            "error": f"Data fetch failed: {str(e)}",
            "status": "error",
        }


async def build_features_node(state: AgentState) -> dict[str, Any]:
    """
    Build model features from raw data.
    """
    try:
        query = state["query"]
        
        # Build complete features (includes location resolution + neighbor fetch)
        features, location, neighbors = await build_features(query)
        
        return {
            "features": features,
            "resolved_location": location,
            "neighbors": neighbors,
            "status": "features_built",
        }
    
    except Exception as e:
        return {
            "error": f"Feature building failed: {str(e)}",
            "status": "error",
        }


def predict_node(state: AgentState) -> dict[str, Any]:
    """
    Run model prediction.
    """
    try:
        features = state.get("features")
        if not features:
            return {"error": "No features available", "status": "error"}
        
        adapter = get_model_adapter()
        prediction = adapter.predict_quantiles(features)
        
        return {
            "prediction": prediction,
            "status": "predicted",
        }
    
    except Exception as e:
        return {
            "error": f"Prediction failed: {str(e)}",
            "status": "error",
        }


def explain_node(state: AgentState) -> dict[str, Any]:
    """
    Generate explanation for prediction.
    """
    try:
        features = state.get("features")
        prediction = state.get("prediction")
        
        if not features or not prediction:
            return {"error": "Missing features or prediction", "status": "error"}
        
        explanation = explain_prediction(features, prediction)
        
        return {
            "explanation": explanation,
            "status": "explained",
        }
    
    except Exception as e:
        return {
            "error": f"Explanation failed: {str(e)}",
            "status": "error",
        }


def render_a2ui_node(state: AgentState) -> dict[str, Any]:
    """
    Build A2UI messages for frontend.
    """
    try:
        prediction = state.get("prediction")
        explanation = state.get("explanation")
        location = state.get("resolved_location")
        neighbors = state.get("neighbors", [])
        query = state["query"]
        
        if not all([prediction, explanation, location]):
            return {"error": "Missing data for UI rendering", "status": "error"}
        
        messages = build_complete_ui(
            prediction=prediction,
            explanation=explanation,
            location=location,
            neighbors=neighbors,
            horizon_months=query.horizon_months,
            k_neighbors=query.k_neighbors or 5,
        )
        
        return {
            "ui_messages": messages,
            "status": "complete",
        }
    
    except Exception as e:
        return {
            "error": f"UI rendering failed: {str(e)}",
            "status": "error",
        }


# Node registry for easy lookup (pipeline nodes)
NODES = {
    "resolve_location": resolve_location_node,
    "fetch_data": fetch_data_node,
    "build_features": build_features_node,
    "predict": predict_node,
    "explain": explain_node,
    "render_a2ui": render_a2ui_node,
}


# =============================================================================
# Chat Agent Nodes
# =============================================================================
# These nodes are used for the conversational chat agent that uses an LLM
# to decide when to call tools and how to respond to users.
# =============================================================================

import json
from .state import ChatAgentState, ChatMessage, PendingToolCall
from .tools import TOOL_DEFINITIONS, execute_tool
from ..llm_client import get_llm_client, ChatMessage as LLMChatMessage, ToolDefinition


# System prompt for the chat agent
SYSTEM_PROMPT = """You are RentRadar, a UK property AI assistant. You help users with rental forecasts, property listings, and investment analysis.

TOOL SELECTION RULES (follow strictly):

1. Rent/Price Questions → get_rent_forecast
   - "What's the rent in X?"
   - "How much to rent in Y?"
   - "Expected rent for..."
   
2. Property Listings → get_property_listings
   - "What's for rent/sale in X?"
   - "Show me properties in Y"
   - "Find listings in Z"
   
3. Investment/ROI Questions → get_investment_analysis
   - "What's my ROI if I buy..."
   - "Should I invest in..."
   - "Is X a good investment?"
   - "Rental yield for..."

4. Location Search → search_location (RARELY NEEDED)
   - Only if location is completely ambiguous
   - Most UK postcodes work directly

CRITICAL: After ANY tool call, you MUST provide a natural, conversational summary. Users see detailed visualizations - your job is to tell the story in plain English.

Response format:
- Write naturally - NO structured headers like "Bottom line:", "Details:", etc.
- Break into 2-3 short paragraphs for readability
- Use ranges instead of exact figures ("7-8%" not "7.83%")
- Be helpful and encouraging
- Add practical advice or offer next steps naturally
- 4-6 sentences typical (longer is fine if adding value)

Example responses:
"You're looking at around £2,400 per month for Camden, typically between £2,000-£2,800 depending on the property.

The market here is quite strong with good demand from professionals. I'd recommend viewing properties quickly as they tend to go fast in this area."

"I found around 45 rental properties in Shoreditch, with most priced between £1,500-£3,200 per month. There's a good mix of studios and 1-2 bedroom apartments available.

The lower end tends to be further from the tube stations, while premium properties near Old Street command higher rents. Let me know if you'd like me to filter by specific criteria like bedrooms or price range."

"A £300k property in UB8 would give you around 8% gross yield with positive monthly cash flow of about £300 per month. That's a solid investment with good returns, especially compared to most London areas which typically offer 4-5% yields.

The area has decent rental demand from Heathrow workers and local professionals, which helps with occupancy. Overall, this looks like a promising buy-to-let opportunity."
"""


def _convert_messages_for_llm(messages: list[ChatMessage]) -> list[LLMChatMessage]:
    """Convert chat state messages to LLM client format."""
    result = []
    for msg in messages:
        llm_msg = LLMChatMessage(
            role=msg["role"],
            content=msg.get("content"),
            tool_call_id=msg.get("tool_call_id"),
            name=msg.get("name"),
        )
        
        # Handle tool calls from assistant
        if msg.get("tool_calls"):
            from ..llm_client import ToolCall
            llm_msg.tool_calls = [
                ToolCall(
                    id=tc["id"],
                    name=tc["name"],
                    arguments=tc["arguments"]
                )
                for tc in msg["tool_calls"]
            ]
        
        result.append(llm_msg)
    
    return result


def _get_tool_definitions() -> list[ToolDefinition]:
    """Get tool definitions for the LLM."""
    return [
        ToolDefinition(
            name=tool["name"],
            description=tool["description"],
            parameters=tool["parameters"],
        )
        for tool in TOOL_DEFINITIONS
    ]


async def chat_node(state: ChatAgentState) -> dict[str, Any]:
    """
    Chat node - calls the LLM to decide what to do.
    
    The LLM can either:
    1. Respond directly with text
    2. Call one or more tools
    """
    try:
        messages = state.get("messages", [])
        
        print(f"[CHAT_NODE] Processing {len(messages)} messages")
        
        # Debug: Print last few messages to see what LLM is getting
        if len(messages) > 1:
            for i, msg in enumerate(messages[-3:]):
                role = msg.get("role")
                content = msg.get("content", "")
                content_preview = content[:100] if content else "[no content]"
                print(f"[CHAT_NODE] Message {i}: role={role}, content_len={len(content or '')}, preview={content_preview}")
        
        # Add system prompt if not present
        if not messages or messages[0].get("role") != "system":
            system_msg: ChatMessage = {
                "role": "system",
                "content": SYSTEM_PROMPT,
            }
            messages = [system_msg] + list(messages)
        
        # Convert to LLM format
        llm_messages = _convert_messages_for_llm(messages)
        tools = _get_tool_definitions()
        
        print(f"[CHAT_NODE] Calling LLM with {len(tools)} tools")
        
        # Call LLM
        client = get_llm_client()
        response = await client.chat_completion(
            messages=llm_messages,
            tools=tools,
            temperature=0.7,
            max_tokens=2048,
        )
        
        print(f"[CHAT_NODE] LLM response - tool_calls: {bool(response.tool_calls)}, content length: {len(response.content or '')}")
        
        # Check if we have tool calls
        if response.tool_calls:
            # Convert tool calls to state format
            pending_calls: list[PendingToolCall] = [
                {
                    "id": tc.id,
                    "name": tc.name,
                    "arguments": tc.arguments,
                }
                for tc in response.tool_calls
            ]
            
            # Add assistant message with tool calls to history
            assistant_msg: ChatMessage = {
                "role": "assistant",
                "content": response.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "name": tc.name,
                        "arguments": tc.arguments,
                    }
                    for tc in response.tool_calls
                ],
            }
            
            return {
                "messages": messages + [assistant_msg],
                "pending_tool_calls": pending_calls,
                "status": "tool_calling",
                "should_continue": True,
            }
        
        else:
            # Direct response - add to messages
            assistant_msg: ChatMessage = {
                "role": "assistant",
                "content": response.content,
            }
            
            return {
                "messages": messages + [assistant_msg],
                "pending_tool_calls": [],
                "stream_output": [{"type": "text", "content": response.content}],
                "status": "complete",
                "should_continue": False,
            }
    
    except Exception as e:
        return {
            "error": f"Chat node failed: {str(e)}",
            "status": "error",
            "should_continue": False,
        }


async def tool_executor_node(state: ChatAgentState) -> dict[str, Any]:
    """
    Tool executor node - executes pending tool calls.
    
    After execution, adds tool results to messages and collects A2UI messages.
    """
    try:
        pending_calls = state.get("pending_tool_calls", [])
        messages = list(state.get("messages", []))
        a2ui_messages = list(state.get("a2ui_messages", []))
        stream_output = list(state.get("stream_output", []))
        current_valuation = state.get("current_valuation")
        
        print(f"[TOOL_EXECUTOR] Executing {len(pending_calls)} tool calls")
        
        if not pending_calls:
            return {
                "status": "no_tools",
                "should_continue": True,
            }
        
        # Execute each tool call
        for tool_call in pending_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["arguments"]
            
            # Notify stream about tool execution
            stream_output.append({
                "type": "tool_start",
                "tool": tool_name,
                "arguments": tool_args,
            })
            
            # Execute the tool
            result = await execute_tool(tool_name, tool_args)
            
            # Collect A2UI messages if present
            if result.get("a2ui_messages"):
                # Extend the list instead of replacing it
                a2ui_messages.extend(result["a2ui_messages"])
                stream_output.append({
                    "type": "a2ui",
                    "messages": result["a2ui_messages"],
                })
            
            # Store valuation if present
            if result.get("prediction"):
                current_valuation = {
                    "prediction": result.get("prediction"),
                    "explanation": result.get("explanation"),
                    "location": result.get("location"),
                    "neighbors": result.get("neighbors"),
                }
            
            # Add tool result to messages - ONLY send summary to LLM, not full data
            # This prevents context window overflow with large datasets
            llm_result = {
                "summary": result.get("summary", "Tool executed successfully"),
                "success": result.get("success", True),
            }
            
            print(f"[TOOL_EXECUTOR] Sending summary to LLM: {llm_result['summary'][:200]}...")
            
            tool_result_msg: ChatMessage = {
                "role": "tool",
                "content": json.dumps(llm_result),
                "tool_call_id": tool_call["id"],
                "name": tool_name,
            }
            messages.append(tool_result_msg)
            
            stream_output.append({
                "type": "tool_end",
                "tool": tool_name,
                "success": result.get("success", True),
            })
        
        print(f"[TOOL_EXECUTOR] Completed {len(pending_calls)} tools, returning with should_continue=True")
        
        return {
            "messages": messages,
            "a2ui_messages": a2ui_messages,
            "current_valuation": current_valuation,
            "stream_output": stream_output,
            "pending_tool_calls": [],
            "status": "tools_executed",
            "should_continue": True,  # Continue to let LLM respond to tool results
        }
    
    except Exception as e:
        return {
            "error": f"Tool execution failed: {str(e)}",
            "status": "error",
            "should_continue": False,
        }


# Chat node registry
CHAT_NODES = {
    "chat": chat_node,
    "tool_executor": tool_executor_node,
}
