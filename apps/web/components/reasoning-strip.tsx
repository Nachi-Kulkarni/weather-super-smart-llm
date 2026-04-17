"use client";

type Props = {
  text: string;
  active?: boolean;
};

/**
 * Collapsible panel for provider reasoning / chain-of-thought streamed as separate NDJSON events.
 */
export function ReasoningStrip({ text, active }: Props) {
  if (!text.trim() && !active) {
    return null;
  }

  return (
    <details className="reasoning-panel" open={Boolean(active && text.trim())}>
      <summary className="reasoning-summary">Reasoning &amp; chain-of-thought</summary>
      <pre className="reasoning-pre">{text.trim() || (active ? "…" : "")}</pre>
    </details>
  );
}
