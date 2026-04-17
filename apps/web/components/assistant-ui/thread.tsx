"use client";

import {
  ComposerPrimitive,
  MessagePartPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
} from "@assistant-ui/react";

import { AssistantMarkdownText } from "@/components/assistant-markdown-text";

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
      <div className="message-label">Advisor</div>
      <MessagePrimitive.Parts
        components={{
          Text: () => <MessagePartPrimitive.Text className="message-text" />,
        }}
      />
    </MessagePrimitive.Root>
  );
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className="message-bubble assistant">
      <div className="message-label">Soil Crop Advisor</div>
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
        rows={4}
        placeholder="Ask for feasible crops, fertilizer burdens, weather-aware ranking, or citation checks..."
      />
      <div className="composer-actions">
        <p className="composer-hint">
          Use the chat for workflow orchestration and the probe panel for the deterministic API contract.
        </p>
        <ComposerPrimitive.Send className="composer-send">
          Send
        </ComposerPrimitive.Send>
      </div>
    </ComposerPrimitive.Root>
  );
}

export function Thread() {
  return (
    <div className="thread-panel">
      <div className="thread-panel-header">
        <p className="eyebrow">Deepagents Runtime</p>
        <h2>Conversation Workbench</h2>
        <p className="panel-copy">
          Streaming NDJSON from `/chat/stream`: markdown answers, live tool traces, and optional model reasoning — orchestrated by the deep agent runtime.
        </p>
      </div>

      <ThreadPrimitive.Root className="thread-root">
        <ThreadPrimitive.Viewport className="thread-viewport">
          <ThreadPrimitive.Empty>
            <div className="thread-empty">
              <p className="empty-title">No advisory thread yet</p>
              <p className="empty-copy">
                Start with a crop-ranking request, ask how confidence is determined, or have the deep agent call the deterministic recommendation tool for you.
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
