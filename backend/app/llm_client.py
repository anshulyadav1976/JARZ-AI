"""
OpenRouter LLM Client with streaming and tool calling support.

This module provides an async wrapper around OpenRouter's API (OpenAI-compatible)
for chat completions with streaming and function/tool calling.
"""
import json
from typing import AsyncGenerator, Optional, Any
from dataclasses import dataclass

import httpx

from .config import get_settings


@dataclass
class ToolDefinition:
    """Definition of a tool that can be called by the LLM."""
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass
class ToolCall:
    """A tool call request from the LLM."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ChatMessage:
    """A chat message in the conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None
    tool_call_id: Optional[str] = None  # For tool responses
    name: Optional[str] = None  # Tool name for tool responses

    def to_dict(self) -> dict:
        """Convert to API-compatible dict."""
        msg = {"role": self.role}
        if self.content is not None:
            msg["content"] = self.content
        if self.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments) if isinstance(tc.arguments, dict) else tc.arguments
                    }
                }
                for tc in self.tool_calls
            ]
        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id
        if self.name:
            msg["name"] = self.name
        return msg


@dataclass
class StreamChunk:
    """A chunk from the streaming response."""
    type: str  # "text", "tool_call", "done"
    content: Optional[str] = None
    tool_call: Optional[ToolCall] = None
    finish_reason: Optional[str] = None


class LLMClient:
    """
    Async client for OpenRouter LLM API.
    
    Uses OpenAI-compatible API through OpenRouter.
    Supports streaming and tool/function calling.
    """
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.openrouter_api_key
        self.model = settings.llm_model
        self.base_url = settings.llm_base_url
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://jarz-rental-valuation.local",
                    "X-Title": "JARZ Rental Valuation"
                },
                timeout=60.0
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    def _build_tools_payload(self, tools: list[ToolDefinition]) -> list[dict]:
        """Convert tool definitions to API format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            }
            for tool in tools
        ]
    
    async def chat_completion(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> ChatMessage:
        """
        Non-streaming chat completion.
        
        Args:
            messages: Conversation history
            tools: Available tools/functions
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            
        Returns:
            Assistant's response message
        """
        client = await self._get_client()
        
        payload = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if tools:
            payload["tools"] = self._build_tools_payload(tools)
            payload["tool_choice"] = "auto"
        
        response = await client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()
        
        print(f"[LLM_CLIENT] API response: {json.dumps(data, indent=2)[:500]}")
        
        choice = data["choices"][0]
        message = choice["message"]
        finish_reason = choice.get("finish_reason")
        
        print(f"[LLM_CLIENT] Finish reason: {finish_reason}")
        print(f"[LLM_CLIENT] Message content: {message.get('content')}")
        print(f"[LLM_CLIENT] Message tool_calls: {message.get('tool_calls')}")
        
        # Parse tool calls if present
        tool_calls = None
        if message.get("tool_calls"):
            tool_calls = []
            for tc in message["tool_calls"]:
                args = tc["function"]["arguments"]
                if isinstance(args, str):
                    args = json.loads(args)
                tool_calls.append(ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=args
                ))
        
        return ChatMessage(
            role="assistant",
            content=message.get("content"),
            tool_calls=tool_calls
        )
    
    async def stream_chat_completion(
        self,
        messages: list[ChatMessage],
        tools: Optional[list[ToolDefinition]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Streaming chat completion.
        
        Args:
            messages: Conversation history
            tools: Available tools/functions
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            
        Yields:
            StreamChunk objects with text or tool calls
        """
        client = await self._get_client()
        
        payload = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        
        if tools:
            payload["tools"] = self._build_tools_payload(tools)
            payload["tool_choice"] = "auto"
        
        # Accumulate tool call data across chunks
        tool_call_accumulator: dict[int, dict] = {}
        
        async with client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                
                data_str = line[6:]  # Remove "data: " prefix
                
                if data_str == "[DONE]":
                    yield StreamChunk(type="done")
                    break
                
                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                
                if not data.get("choices"):
                    continue
                
                choice = data["choices"][0]
                delta = choice.get("delta", {})
                finish_reason = choice.get("finish_reason")
                
                # Handle text content
                if delta.get("content"):
                    yield StreamChunk(
                        type="text",
                        content=delta["content"]
                    )
                
                # Handle tool calls (accumulated across chunks)
                if delta.get("tool_calls"):
                    for tc_delta in delta["tool_calls"]:
                        idx = tc_delta.get("index", 0)
                        
                        if idx not in tool_call_accumulator:
                            tool_call_accumulator[idx] = {
                                "id": "",
                                "name": "",
                                "arguments": ""
                            }
                        
                        acc = tool_call_accumulator[idx]
                        
                        if tc_delta.get("id"):
                            acc["id"] = tc_delta["id"]
                        if tc_delta.get("function", {}).get("name"):
                            acc["name"] = tc_delta["function"]["name"]
                        if tc_delta.get("function", {}).get("arguments"):
                            acc["arguments"] += tc_delta["function"]["arguments"]
                
                # When finished, emit accumulated tool calls
                if finish_reason == "tool_calls":
                    for idx in sorted(tool_call_accumulator.keys()):
                        acc = tool_call_accumulator[idx]
                        try:
                            args = json.loads(acc["arguments"]) if acc["arguments"] else {}
                        except json.JSONDecodeError:
                            args = {}
                        
                        yield StreamChunk(
                            type="tool_call",
                            tool_call=ToolCall(
                                id=acc["id"],
                                name=acc["name"],
                                arguments=args
                            )
                        )
                    yield StreamChunk(type="done", finish_reason="tool_calls")
                    break
                
                if finish_reason == "stop":
                    yield StreamChunk(type="done", finish_reason="stop")
                    break


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get singleton LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
