"use client";

import {
  ThreadListItemPrimitive,
  ThreadListPrimitive,
} from "@assistant-ui/react";

function ThreadListItem() {
  return (
    <ThreadListItemPrimitive.Root className="thread-list-item">
      <ThreadListItemPrimitive.Trigger className="thread-list-trigger">
        <ThreadListItemPrimitive.Title fallback="Untitled thread" />
      </ThreadListItemPrimitive.Trigger>
      <div className="thread-list-actions">
        <ThreadListItemPrimitive.Archive className="thread-list-action">
          Archive
        </ThreadListItemPrimitive.Archive>
        <ThreadListItemPrimitive.Delete className="thread-list-action danger">
          Delete
        </ThreadListItemPrimitive.Delete>
      </div>
    </ThreadListItemPrimitive.Root>
  );
}

export function ThreadList() {
  return (
    <aside className="thread-list-panel">
      <div className="thread-list-header">
        <p className="eyebrow">Assistant-ui</p>
        <h2>Field Threads</h2>
        <p className="panel-copy">
          Thread history is ready for LangGraph-backed conversations and can be swapped for a custom DB-backed thread list later.
        </p>
      </div>

      <ThreadListPrimitive.Root className="thread-list-root">
        <ThreadListPrimitive.New className="thread-new-button">
          Start advisory thread
        </ThreadListPrimitive.New>
        <ThreadListPrimitive.Items
          components={{
            ThreadListItem,
          }}
        />
      </ThreadListPrimitive.Root>
    </aside>
  );
}
