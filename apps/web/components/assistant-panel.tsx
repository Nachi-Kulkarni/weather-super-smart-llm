"use client";

import type { ChatModelAdapter } from "@assistant-ui/react";
import { AssistantRuntimeProvider, useLocalRuntime } from "@assistant-ui/react";
import { useMemo, useState } from "react";

import { Thread } from "@/components/assistant-ui/thread";
import { ReasoningStrip } from "@/components/reasoning-strip";
import { ToolTraceStrip, type ToolEvent } from "@/components/tool-trace-strip";

type NdJsonEvent = {
  type: string;
  delta?: string;
  /** Present on `type: "error"` lines from the API. */
  message?: string;
  tool?: string;
  phase?: ToolEvent["phase"];
  detail?: string | null;
  at?: string | null;
  fullText?: string;
  toolEvents?: ToolEvent[];
};

function parseNdjsonLine(line: string): NdJsonEvent | null {
  const trimmed = line.trim();
  if (!trimmed) {
    return null;
  }
  try {
    return JSON.parse(trimmed) as NdJsonEvent;
  } catch {
    return null;
  }
}

export function AssistantPanel() {
  const [toolEvents, setToolEvents] = useState<ToolEvent[]>([]);
  const [reasoningText, setReasoningText] = useState("");
  const [agentBusy, setAgentBusy] = useState(false);

  const deepAgentAdapter: ChatModelAdapter = useMemo(
    () => ({
      async *run({ messages, abortSignal }) {
        setAgentBusy(true);
        setToolEvents([]);
        setReasoningText("");
        let full = "";
        try {
          const response = await fetch("/api/chat/stream", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ messages }),
            signal: abortSignal,
          });

          if (!response.ok) {
            throw new Error(await response.text());
          }

          const reader = response.body?.getReader();
          if (!reader) {
            throw new Error("No response body for stream");
          }

          const decoder = new TextDecoder();
          let buffer = "";

          const handleEvent = (ev: NdJsonEvent) => {
            const t = ev.type;
            if (t === "text" && typeof ev.delta === "string") {
              full += ev.delta;
              return {
                content: [
                  {
                    type: "text" as const,
                    text: full,
                  },
                ],
              };
            }
            if (t === "reasoning" && typeof ev.delta === "string") {
              setReasoningText((prev) =>
                prev ? `${prev}\n${ev.delta}` : ev.delta!,
              );
              return undefined;
            }
            if (
              t === "tool" &&
              ev.tool &&
              ev.phase &&
              ["start", "end", "error"].includes(ev.phase)
            ) {
              const row: ToolEvent = {
                tool: ev.tool,
                phase: ev.phase,
                detail: ev.detail ?? null,
                at: ev.at ?? null,
              };
              setToolEvents((prev) => [...prev, row]);
              return undefined;
            }
            if (t === "error" && typeof ev.message === "string") {
              full += `${full ? "\n\n" : ""}[stream error] ${ev.message}`;
              return {
                content: [{ type: "text" as const, text: full }],
              };
            }
            if (t === "done") {
              if (typeof ev.fullText === "string") {
                full = ev.fullText;
              }
              if (Array.isArray(ev.toolEvents) && ev.toolEvents.length > 0) {
                setToolEvents(ev.toolEvents);
              }
            }
            return undefined;
          };

          while (true) {
            const { done, value } = await reader.read();
            if (done) {
              break;
            }
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() ?? "";
            for (const line of lines) {
              const ev = parseNdjsonLine(line);
              if (!ev) {
                continue;
              }
              const out = handleEvent(ev);
              if (out) {
                yield out;
              }
            }
          }

          const tail = parseNdjsonLine(buffer);
          if (tail) {
            const out = handleEvent(tail);
            if (out) {
              yield out;
            }
          }

          yield {
            content: [
              {
                type: "text",
                text: full,
              },
            ],
          };
        } finally {
          setAgentBusy(false);
        }
      },
    }),
    [],
  );

  const runtime = useLocalRuntime(deepAgentAdapter);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <section className="assistant-shell">
        <ReasoningStrip text={reasoningText} active={agentBusy} />
        <ToolTraceStrip events={toolEvents} isRunning={agentBusy} live />
        <Thread />
      </section>
    </AssistantRuntimeProvider>
  );
}
