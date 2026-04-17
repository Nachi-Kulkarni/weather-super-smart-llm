"use client";

export type ToolEvent = {
  tool: string;
  phase: "start" | "end" | "error";
  detail?: string | null;
  at?: string | null;
};

type Props = {
  events: ToolEvent[];
  isRunning?: boolean;
  live?: boolean;
};

/** Collapse raw start/end/error events into one row per tool invocation. */
type CollapsedTool = {
  tool: string;
  status: "running" | "done" | "error";
  detail?: string | null;
};

function collapseEvents(events: ToolEvent[]): CollapsedTool[] {
  const map = new Map<string, CollapsedTool>();

  for (const ev of events) {
    const key = ev.tool;
    const existing = map.get(key);

    if (ev.phase === "start") {
      map.set(key, { tool: ev.tool, status: "running" });
    } else if (ev.phase === "end") {
      map.set(key, { tool: ev.tool, status: "done" });
    } else if (ev.phase === "error") {
      map.set(key, { tool: ev.tool, status: "error", detail: ev.detail });
    }
  }

  return Array.from(map.values());
}

export function ToolTraceStrip({ events, isRunning }: Props) {
  const tools = collapseEvents(events);

  if (!tools.length && !isRunning) {
    return null;
  }

  // Only show tools that are still running — hide finished ones
  const running = tools.filter((t) => t.status === "running");

  return (
    <div className="tool-trace-inline tool-trace-live">
      <ol className="tool-trace-list">
        {running.map((t) => (
          <li className="tool-trace-item tool-phase-start" key={t.tool}>
            <span className="tool-trace-icon">
              <span className="tool-icon-spin">&#9696;</span>
            </span>
            <span className="tool-trace-name">{humanizeToolName(t.tool)}</span>
          </li>
        ))}
        {isRunning && !running.length && (
          <li className="tool-trace-item tool-phase-start">
            <span className="tool-trace-icon">
              <span className="tool-icon-spin">&#9696;</span>
            </span>
            <span className="tool-trace-name">Thinking...</span>
          </li>
        )}
      </ol>
    </div>
  );
}

function humanizeToolName(name: string) {
  return name.replace(/_/g, " ");
}
