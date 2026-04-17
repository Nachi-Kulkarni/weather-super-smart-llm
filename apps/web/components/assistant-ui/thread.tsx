"use client";

import {
  ComposerPrimitive,
  MessagePartPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
} from "@assistant-ui/react";

import { AssistantMarkdownText } from "@/components/assistant-markdown-text";
import { useStreamState } from "@/components/assistant-panel";
import { ToolTraceStrip } from "@/components/tool-trace-strip";

const suggestions = [
  {
    label: "Rank Karnataka crops",
    prompt:
      "Rank feasible crops for a Karnataka farmer with soil N 180, P 22, K 180 and a kharif window.",
  },
  {
    label: "Explain confidence bands",
    prompt: "Explain how confidence bands A, B, and C are assigned.",
  },
  {
    label: "Show retrieval order",
    prompt:
      "Show the retrieval order between district STCR, state STCR, agro-region STCR, and fallback sources.",
  },
];

function UserMessage() {
  return (
    <MessagePrimitive.Root className="message-bubble user">
      <div className="message-label">You</div>
      <MessagePrimitive.Parts
        components={{
          Text: () => <MessagePartPrimitive.Text className="message-text" />,
        }}
      />
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  const { toolEvents, agentBusy } = useStreamState();

  return (
    <MessagePrimitive.Root className="message-bubble assistant">
      <div className="message-label">Soil Crop Advisor</div>

      {/* Inline tool activity — Perplexity-style */}
      {(toolEvents.length > 0 || agentBusy) && (
        <div className="message-tools">
          <ToolTraceStrip events={toolEvents} isRunning={agentBusy} live />
        </div>
      )}

      <MessagePrimitive.Parts
        components={{
          Text: AssistantMarkdownText,
        }}
      />
    </MessagePrimitive.Root>
  );
}

function Composer() {
  return (
    <ComposerPrimitive.Root className="composer-root">
      <ComposerPrimitive.Input
        className="composer-input"
        rows={1}
        placeholder="Ask about crops, fertilizer, weather risk..."
      />
      <ComposerPrimitive.Send className="composer-send">
        Send
      </ComposerPrimitive.Send>
    </ComposerPrimitive.Root>
  );
}

export function Thread() {
  return (
    <div className="thread-panel">
      <div className="thread-panel-header">
        <p className="eyebrow">Soil Crop Advisor</p>
        <h2>Ask about crops, soil, or fertilizer</h2>
      </div>

      <ThreadPrimitive.Root className="thread-root">
        <ThreadPrimitive.Viewport className="thread-viewport">
          <ThreadPrimitive.Empty>
            <div className="thread-empty">
              <p className="empty-title">What would you like to know?</p>
              <p className="empty-copy">
                Ask for crop rankings, fertilizer recommendations, weather-aware
                analysis, or how confidence scores work.
              </p>
              <div className="suggestion-grid">
                {suggestions.map((suggestion) => (
                  <ThreadPrimitive.Suggestion
                    className="suggestion-chip"
                    key={suggestion.label}
                    prompt={suggestion.prompt}
                  >
                    {suggestion.label}
                  </ThreadPrimitive.Suggestion>
                ))}
              </div>
            </div>
          </ThreadPrimitive.Empty>
          <ThreadPrimitive.Messages
            components={{
              UserMessage,
              AssistantMessage,
            }}
          />
          <ThreadPrimitive.ScrollToBottom className="scroll-button">
            Jump to latest
          </ThreadPrimitive.ScrollToBottom>
        </ThreadPrimitive.Viewport>
        <Composer />
      </ThreadPrimitive.Root>
    </div>
  );
}
