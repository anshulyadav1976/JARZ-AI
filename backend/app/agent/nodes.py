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
SYSTEM_PROMPT = """You are JARZ, an expert AI assistant for UK rental property valuation. You help users understand rental prices, market trends, and property valuations across the UK.

Your capabilities:
1. **Rental Forecasting**: Predict future rental prices with confidence intervals (P10/P50/P90)
2. **Location Analysis**: Search and validate UK postcodes and areas
3. **Market Insights**: Explain factors driving rental prices using data-driven analysis

When users ask about rental prices, valuations, or forecasts:
- Use the get_rent_forecast tool to generate predictions
- Always explain what the numbers mean in plain language
- Highlight key drivers affecting the prediction

When answering questions:
- Be concise but informative
- Use specific numbers and data when available
- Explain complex concepts in simple terms
- If you're unsure about a location, use search_location first

For UK postcodes, common formats include: NW1, E14, SW1A, EC2A, W1, SE1, etc.

You render visualizations automatically when running forecasts - the user will see charts, maps, and driver analysis alongside your text response."""


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
        
        # Call LLM
        client = get_llm_client()
        response = await client.chat_completion(
            messages=llm_messages,
            tools=tools,
            temperature=0.7,
            max_tokens=2048,
        )
        
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
                a2ui_messages = result["a2ui_messages"]
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
            
            # Add tool result to messages
            tool_result_msg: ChatMessage = {
                "role": "tool",
                "content": json.dumps(result, default=str),
                "tool_call_id": tool_call["id"],
                "name": tool_name,
            }
            messages.append(tool_result_msg)
            
            stream_output.append({
                "type": "tool_end",
                "tool": tool_name,
                "success": result.get("success", True),
            })
        
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
