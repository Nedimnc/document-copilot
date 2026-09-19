import { NavLink } from "react-router-dom"

import type { ChatThread } from "@/lib/chat"

function threadLabel(thread: ChatThread): string {
  const title = thread.title?.trim()
  return title || "New chat"
}

export function ThreadSidebar({
  threads,
  email,
  creating,
  onCreate,
  onSignOut,
}: {
  threads: ChatThread[]
  email: string | null
  creating: boolean
  onCreate: () => void
  onSignOut: () => void
}) {
  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-zinc-200 bg-white">
      <div className="flex items-center justify-between gap-2 border-b border-zinc-200 px-3 py-3">
        <NavLink className="text-sm font-medium text-zinc-900" to="/">
          Document Copilot
        </NavLink>
        <button
          className="rounded-md bg-zinc-900 px-2 py-1 text-xs text-white disabled:opacity-60"
          type="button"
          disabled={creating}
          onClick={onCreate}
        >
          {creating ? "…" : "New"}
        </button>
      </div>

      <nav className="min-h-0 flex-1 overflow-y-auto p-2">
        {threads.length === 0 ? (
          <p className="px-2 py-3 text-sm text-zinc-500">No conversations yet.</p>
        ) : (
          <ul className="space-y-1">
            {threads.map((thread) => (
              <li key={thread.id}>
                <NavLink
                  to={`/chats/${thread.id}`}
                  className={({ isActive }) =>
                    `block truncate rounded-md px-2 py-2 text-sm ${
                      isActive
                        ? "bg-zinc-900 text-white"
                        : "text-zinc-700 hover:bg-zinc-100"
                    }`
                  }
                >
                  {threadLabel(thread)}
                </NavLink>
              </li>
            ))}
          </ul>
        )}
      </nav>

      <div className="border-t border-zinc-200 px-3 py-3">
        <p className="truncate text-xs text-zinc-500">{email ?? "Signed in"}</p>
        <button
          className="mt-2 text-xs text-zinc-600 underline"
          type="button"
          onClick={onSignOut}
        >
          Sign out
        </button>
      </div>
    </aside>
  )
}
