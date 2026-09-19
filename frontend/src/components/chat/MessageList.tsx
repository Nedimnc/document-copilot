import { useEffect, useRef } from "react"
import type { UIMessage } from "ai"

import { messageText } from "@/lib/chat"

export function MessageList({
  messages,
  status,
}: {
  messages: UIMessage[]
  status: "submitted" | "streaming" | "ready" | "error"
}) {
  const bottom = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "end" })
  }, [messages, status])

  if (messages.length === 0 && status === "ready") {
    return (
      <div className="flex flex-1 items-center justify-center px-6 text-center text-sm text-zinc-500">
        Ask a question. The reply is stubbed until retrieval is wired.
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <ol className="mx-auto flex max-w-2xl flex-col gap-4">
        {messages.map((message) => {
          const isUser = message.role === "user"
          return (
            <li
              key={message.id}
              className={`max-w-[85%] rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
                isUser
                  ? "self-end bg-zinc-900 text-white"
                  : "self-start bg-white text-zinc-900 shadow-sm ring-1 ring-zinc-200"
              }`}
            >
              {messageText(message) || (isUser ? "" : "…")}
            </li>
          )
        })}
      </ol>
      {status === "submitted" || status === "streaming" ? (
        <p className="mx-auto mt-3 max-w-2xl text-sm text-zinc-500">Streaming…</p>
      ) : null}
      <div ref={bottom} />
    </div>
  )
}
