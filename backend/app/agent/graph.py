"""LangGraph workflow definition."""
from typing import Any, AsyncGenerator
from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import (
    resolve_location_node,
    fetch_data_node,
    build_features_node,
    predict_node,
    explain_node,
    render_a2ui_node,
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
