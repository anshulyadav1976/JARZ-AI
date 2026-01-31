"""LangGraph agent state definition."""
from typing import Any, Optional, TypedDict
from ..schemas import (
    UserQuery,
    ModelFeatures,
    PredictionResult,
    ExplanationResult,
    ResolvedLocation,
    Neighbor,
)


class AgentState(TypedDict, total=False):
    """
    State passed through the agent workflow.
    
    This is used for the direct pipeline (form-based input).
    """
    
    # Input
    query: UserQuery
    
    # Resolved data
    resolved_location: Optional[ResolvedLocation]
    
    # Raw fetched data from ScanSan
    raw_data: Optional[dict[str, Any]]
    
    # Built features
    features: Optional[ModelFeatures]
    
    # Model outputs
    prediction: Optional[PredictionResult]
    
    # Explanation
    explanation: Optional[ExplanationResult]
    
    # Neighbors for spatial visualization
    neighbors: list[Neighbor]
    
    # A2UI messages to stream
    ui_messages: list[dict[str, Any]]
    
    # Error state
    error: Optional[str]
    
    # Processing status
    status: str


class ChatMessage(TypedDict, total=False):
    """A message in the chat conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: Optional[str]
    tool_calls: Optional[list[dict]]
    tool_call_id: Optional[str]
    name: Optional[str]


class PendingToolCall(TypedDict):
    """A pending tool call to be executed."""
    id: str
    name: str
    arguments: dict[str, Any]


class ChatAgentState(TypedDict, total=False):
    """
    State for the chat-based conversational agent.
    
    This agent uses an LLM to decide when to call tools and how to respond.
    """
    
    # Chat history - list of messages
    messages: list[ChatMessage]
    
    # Pending tool calls from the LLM
    pending_tool_calls: list[PendingToolCall]
    
    # A2UI messages to render in the side panel
    a2ui_messages: list[dict[str, Any]]
    
    # Current valuation result (if any)
    current_valuation: Optional[dict[str, Any]]
    
    # Stream output - text chunks and events to send to frontend
    stream_output: list[dict[str, Any]]
    
    # Error state
    error: Optional[str]
    
    # Processing status
    status: str  # "thinking", "tool_calling", "responding", "complete", "error"
    
    # Whether the agent should continue (tool calling loop)
    should_continue: bool
