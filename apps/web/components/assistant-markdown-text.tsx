"use client";

import { MessagePartPrimitive } from "@assistant-ui/react";
import type { ComponentProps } from "react";
import { forwardRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type DivProps = ComponentProps<"div">;

/**
 * Renders assistant message text as GitHub-flavored markdown (tables, lists, code fences).
 * `smooth` is disabled so token streaming from the server is not double-animated.
 */
const MarkdownShell = forwardRef<HTMLDivElement, DivProps>(function MarkdownShell(
  { children, className, ...rest },
  ref,
) {
  const raw = String(children ?? "");
  return (
    <div
      ref={ref}
      {...rest}
      className={`assistant-markdown message-text${className ? ` ${className}` : ""}`}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{raw}</ReactMarkdown>
    </div>
  );
});

export function AssistantMarkdownText() {
  return <MessagePartPrimitive.Text component={MarkdownShell} smooth={false} />;
}
