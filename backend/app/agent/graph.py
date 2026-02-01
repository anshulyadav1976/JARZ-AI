"""LangGraph workflow definition."""
from typing import Any, AsyncGenerator
from langgraph.graph import StateGraph, END

from .state import AgentState, ChatAgentState, ChatMessage
from .nodes import (
    resolve_location_node,
    fetch_data_node,
    build_features_node,
    predict_node,
    explain_node,
    render_a2ui_node,
    chat_node,
    tool_executor_node,
)
from ..schemas import UserQuery


def should_continue(state: AgentState) -> str:
    """Determine next step based on state."""
    if state.get("error"):
        return "error"
    return "continue"


def build_graph() -> StateGraph:
    """
    Build the LangGraph workflow for rental valuation.
    
    Flow:
    ResolveLocation -> FetchData -> BuildFeatures -> Predict -> Explain -> RenderA2UI
    """
    # Create state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("resolve_location", resolve_location_node)
    workflow.add_node("fetch_data", fetch_data_node)
    workflow.add_node("build_features", build_features_node)
    workflow.add_node("predict", predict_node)
    workflow.add_node("explain", explain_node)
    workflow.add_node("render_a2ui", render_a2ui_node)
    
    # Set entry point
    workflow.set_entry_point("resolve_location")
    
    # Add edges (linear flow for now)
    workflow.add_edge("resolve_location", "fetch_data")
    workflow.add_edge("fetch_data", "build_features")
    workflow.add_edge("build_features", "predict")
    workflow.add_edge("predict", "explain")
    workflow.add_edge("explain", "render_a2ui")
    workflow.add_edge("render_a2ui", END)
    
    return workflow


# Compiled graph singleton
_compiled_graph = None


def get_graph():
    """Get compiled graph (singleton)."""
    global _compiled_graph
    if _compiled_graph is None:
        workflow = build_graph()
        _compiled_graph = workflow.compile()
    return _compiled_graph


async def run_agent(query: UserQuery) -> AgentState:
    """
    Run the agent workflow.
    
    Args:
        query: User query for rental valuation
        
    Returns:
        Final agent state with prediction and UI messages
    """
    graph = get_graph()
    
    initial_state: AgentState = {
        "query": query,
        "resolved_location": None,
        "raw_data": None,
        "features": None,
        "prediction": None,
        "explanation": None,
        "neighbors": [],
        "ui_messages": [],
        "error": None,
        "status": "started",
    }
    
    # Run the graph
    final_state = await graph.ainvoke(initial_state)
    
    return final_state


async def stream_agent(query: UserQuery) -> AsyncGenerator[dict[str, Any], None]:
    """
    Stream agent execution, yielding state updates.
    
    Args:
        query: User query for rental valuation
        
    Yields:
        State updates as the agent progresses
    """
    graph = get_graph()
    
    initial_state: AgentState = {
        "query": query,
        "resolved_location": None,
        "raw_data": None,
        "features": None,
        "prediction": None,
        "explanation": None,
        "neighbors": [],
        "ui_messages": [],
        "error": None,
        "status": "started",
    }
    
    # Stream through the graph
    async for event in graph.astream(initial_state):
        # Yield each node's output
        for node_name, node_output in event.items():
            yield {
                "node": node_name,
                "output": node_output,
            }


# =============================================================================
# Chat Agent Graph
# =============================================================================
# This graph handles conversational interactions with tool calling.
# Flow: Chat -> (Tool Executor -> Chat)* -> End
# =============================================================================

def chat_should_continue(state: ChatAgentState) -> str:
    """Determine if chat agent should continue or end."""
    if state.get("error"):
        return "end"
    if not state.get("should_continue", False):
        return "end"
    if state.get("pending_tool_calls"):
        return "execute_tools"
    return "respond"


def build_chat_graph() -> StateGraph:
    """
    Build the LangGraph workflow for chat-based agent.
    
    Flow:
    Chat Node -> (if tool calls) -> Tool Executor -> Chat Node
              -> (if response) -> End
    """
    workflow = StateGraph(ChatAgentState)
    
    # Add nodes
    workflow.add_node("chat", chat_node)
    workflow.add_node("tool_executor", tool_executor_node)
    
    # Set entry point
    workflow.set_entry_point("chat")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "chat",
        chat_should_continue,
        {
            "execute_tools": "tool_executor",
            "respond": END,
            "end": END,
        }
    )
    
    # After tool execution, go back to chat to respond
    workflow.add_edge("tool_executor", "chat")
    
    return workflow


# Compiled chat graph singleton
_compiled_chat_graph = None


def get_chat_graph():
    """Get compiled chat graph (singleton)."""
    global _compiled_chat_graph
    if _compiled_chat_graph is None:
        workflow = build_chat_graph()
        _compiled_chat_graph = workflow.compile()
    return _compiled_chat_graph


async def run_chat_agent(
    user_message: str,
    history: list[ChatMessage] = None,
) -> ChatAgentState:
    """
    Run the chat agent with a user message.
    
    Args:
        user_message: The user's message
        history: Previous conversation history (optional)
        
    Returns:
        Final agent state with response and any A2UI messages
    """
    graph = get_chat_graph()
    
    # Build messages list
    messages: list[ChatMessage] = []
    if history:
        messages.extend(history)
    
    # Add user message
    messages.append({
        "role": "user",
        "content": user_message,
    })
    
    initial_state: ChatAgentState = {
        "messages": messages,
        "pending_tool_calls": [],
        "a2ui_messages": [],
        "current_valuation": None,
        "stream_output": [],
        "error": None,
        "status": "thinking",
        "should_continue": True,
    }
    
    # Run the graph
    final_state = await graph.ainvoke(initial_state)
    
    return final_state


async def stream_chat_agent(
    user_message: str,
    history: list[ChatMessage] = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Stream chat agent execution.
    
    Args:
        user_message: The user's message
        history: Previous conversation history (optional)
        
    Yields:
        Events as the agent processes (text chunks, tool calls, A2UI messages)
    """
    graph = get_chat_graph()
    
    # Build messages list
    messages: list[ChatMessage] = []
    if history:
        messages.extend(history)
    
    # Add user message
    messages.append({
        "role": "user",
        "content": user_message,
    })
    
    initial_state: ChatAgentState = {
        "messages": messages,
        "pending_tool_calls": [],
        "a2ui_messages": [],
        "current_valuation": None,
        "stream_output": [],
        "error": None,
        "status": "thinking",
        "should_continue": True,
    }
    
    # Stream through the graph (each node's stream_output is that node's output only)
    async for event in graph.astream(initial_state):
        for node_name, node_output in event.items():
            print(f"[GRAPH] Processing node: {node_name}, status: {node_output.get('status')}")
            
            # Yield node info
            yield {
                "type": "node",
                "node": node_name,
                "status": node_output.get("status"),
            }
            
            # Yield all stream output from this node (per-node, not cumulative)
            stream_output = node_output.get("stream_output", [])
            print(f"[GRAPH] Node {node_name} has {len(stream_output)} stream_output items")
            for i, item in enumerate(stream_output):
                print(f"[GRAPH] Yielding stream_output item {i}: type={item.get('type')}, content_len={len(item.get('content', ''))}")
                yield item
            
            # Yield error if present
            if node_output.get("error"):
                yield {
                    "type": "error",
                    "error": node_output["error"],
                }
            
            # Yield final state info when complete (text already yielded via stream_output)
            if node_output.get("status") == "complete":
                yield {
                    "type": "complete",
                    "a2ui_messages": node_output.get("a2ui_messages", []),
                }
