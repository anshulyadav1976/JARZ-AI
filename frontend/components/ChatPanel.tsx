"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { ChatMessage, Message, TypingIndicator, ToolIndicator } from "./ChatMessage";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageSquare, Send, Loader2, PanelRightClose, PanelRight } from "lucide-react";

interface ChatPanelProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  currentTool?: { name: string; isRunning: boolean } | null;
  streamingContent?: string;
  onTogglePanel: () => void;
  showPanel: boolean;
}

export function ChatPanel({
  messages,
  onSendMessage,
  isLoading,
  currentTool,
  streamingContent,
  onTogglePanel,
  showPanel,
}: ChatPanelProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent, scrollToBottom]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;
    onSendMessage(trimmed);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const displayMessages = [...messages];
  if (streamingContent) {
    const lastMsg = displayMessages[displayMessages.length - 1];
    if (lastMsg && lastMsg.role === "assistant" && lastMsg.isStreaming) {
      displayMessages[displayMessages.length - 1] = { ...lastMsg, content: streamingContent };
    } else {
      displayMessages.push({ id: "streaming", role: "assistant", content: streamingContent, isStreaming: true });
    }
  }

  return (
    <div className="flex flex-col h-full bg-background">
      <div className="flex-shrink-0 px-6 py-4">
        <div className="flex items-center justify-end">
          <Button
            variant={showPanel ? "default" : "outline"}
            size="sm"
            onClick={onTogglePanel}
            className="gap-2"
          >
            {showPanel ? <PanelRightClose className="h-4 w-4" /> : <PanelRight className="h-4 w-4" />}
            <span className="hidden sm:inline">{showPanel ? "Hide" : "Show"} Insights</span>
          </Button>
        </div>
      </div>
      
      <ScrollArea className="flex-1 px-6 pt-6">
        {displayMessages.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-blue-600/20 to-purple-600/20 rounded-full flex items-center justify-center">
              <MessageSquare className="w-8 h-8 text-primary" />
            </div>
            <h3 className="text-lg font-medium mb-2">Welcome to RentRadar</h3>
            <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto">
              Get AI-powered rental valuations, market analysis, and property insights.
            </p>
            <div className="space-y-2 max-w-md mx-auto">
              {[
                "What's the rent forecast for NW1?",
                "Tell me about Camden's rental market",
                "Show me a 12-month forecast for E14",
              ].map((suggestion, idx) => (
                <Button
                  key={idx}
                  variant="outline"
                  className="w-full justify-start text-left font-normal"
                  onClick={() => { setInput(suggestion); inputRef.current?.focus(); }}
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        )}

        <div className="py-4 space-y-4">
          {displayMessages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {currentTool && <ToolIndicator toolName={currentTool.name} isRunning={currentTool.isRunning} />}
          {isLoading && !streamingContent && !currentTool && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      <div className="flex-shrink-0 border-t px-6 py-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about rental valuations..."
            disabled={isLoading}
            rows={1}
            className="flex-1 px-4 py-3 rounded-lg border bg-background resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
            style={{ minHeight: "48px", maxHeight: "120px" }}
          />
          <Button type="submit" size="icon" disabled={!input.trim() || isLoading} className="h-12 w-12">
            {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
          </Button>
        </form>
        <p className="text-xs text-muted-foreground mt-2 text-center">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
