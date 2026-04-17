"use client";

import type { ChatModelAdapter } from "@assistant-ui/react";
import { AssistantRuntimeProvider, useLocalRuntime } from "@assistant-ui/react";
import { createContext, useContext, useMemo, useState } from "react";

import { Thread } from "@/components/assistant-ui/thread";
import type { ToolEvent } from "@/components/tool-trace-strip";

type StreamState = {
  toolEvents: ToolEvent[];
  agentBusy: boolean;
};

const StreamContext = createContext<StreamState>({
  toolEvents: [],
  agentBusy: false,
});

export function useStreamState() {
  return useContext(StreamContext);
}

export function AssistantPanel() {
  const [toolEvents, setToolEvents] = useState<ToolEvent[]>([]);
  const [agentBusy, setAgentBusy] = useState(false);

  const deepAgentAdapter: ChatModelAdapter = useMemo(
    () => ({
      async *run({ messages, abortSignal }) {
        setAgentBusy(true);
        setToolEvents([]);

        try {
          const response = await fetch("/api/chat", {
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

          const data = (await response.json()) as {
            text: string;
            toolEvents?: ToolEvent[];
          };

          // Show tool events if present
          if (Array.isArray(data.toolEvents) && data.toolEvents.length > 0) {
            setToolEvents(data.toolEvents);
          }

          yield {
            content: [
              {
                type: "text" as const,
                text: data.text || "",
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
    <StreamContext.Provider value={{ toolEvents, agentBusy }}>
      <AssistantRuntimeProvider runtime={runtime}>
        <section className="assistant-shell">
          <Thread />
        </section>
      </AssistantRuntimeProvider>
    </StreamContext.Provider>
  );
}
