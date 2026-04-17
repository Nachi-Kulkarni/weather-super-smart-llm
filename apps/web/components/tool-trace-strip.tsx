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
  /** When true, skip stagger animation so live streamed tool rows appear immediately. */
  live?: boolean;
};

/**
 * Visualizes deep-agent tool calls. For buffered (non-streaming) responses we replay with CSS delays;
 * for `/chat/stream` use `live` so start/end lines show up as they arrive.
 */
export function ToolTraceStrip({ events, isRunning, live }: Props) {
  if (!events.length && !isRunning) {
    return null;
  }

  return (
    <div className={`tool-trace${live ? " tool-trace-live" : ""}`} aria-live="polite">
      <div className="tool-trace-header">
        <span className="tool-trace-pulse" aria-hidden />
        <span>Tool activity</span>
        {isRunning ? <span className="tool-trace-running">Running…</span> : null}
      </div>
      <ol className="tool-trace-list">
        {events.map((event, index) => (
          <li
            className={`tool-trace-item tool-phase-${event.phase}`}
            key={`${event.tool}-${event.at ?? index}-${index}`}
            style={
              live
                ? undefined
                : { animationDelay: `${index * 90}ms` }
            }
          >
            <span className="tool-trace-name">{humanizeToolName(event.tool)}</span>
            <span className="tool-trace-phase">{phaseLabel(event.phase)}</span>
            {event.detail &&
            (event.phase === "error" || event.phase === "start") ? (
              <span
                className={
                  event.phase === "error"
                    ? "tool-trace-detail"
                    : "tool-trace-detail tool-trace-detail-muted"
                }
              >
                {event.detail}
              </span>
            ) : null}
          </li>
        ))}
      </ol>
    </div>
  );
}

function humanizeToolName(name: string) {
  return name.replace(/_/g, " ");
}

function phaseLabel(phase: ToolEvent["phase"]) {
  if (phase === "start") {
    return "started";
  }
  if (phase === "error") {
    return "error";
  }
  return "done";
}
