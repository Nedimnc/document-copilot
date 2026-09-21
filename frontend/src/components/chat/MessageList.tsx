import { useEffect, useRef } from "react"
import type { UIMessage } from "ai"

import { Message } from "@/components/chat/Message"
import type { MessageCitation } from "@/lib/citations"
import { visibleChatMessages, type ChatStatus } from "@/lib/chat"

const STICK_THRESHOLD_PX = 80

export function MessageList({
  messages,
  status,
  citationsByMessageId,
}: {
  messages: UIMessage[]
  status: ChatStatus
  citationsByMessageId: Record<string, MessageCitation[]>
}) {
  const container = useRef<HTMLDivElement>(null)
  // Follow new content only while the user is already near the bottom. Once they
  // scroll up to read, we stop yanking them back down until they return.
  const stick = useRef(true)

  function onScroll() {
    const el = container.current
    if (!el) return
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    stick.current = distanceFromBottom < STICK_THRESHOLD_PX
  }

  useEffect(() => {
    const el = container.current
    if (el && stick.current) {
      el.scrollTop = el.scrollHeight
    }
  }, [messages, status, citationsByMessageId])

  const visibleMessages = visibleChatMessages(messages, status)
  const waiting = status === "submitted" || status === "streaming"

  return (
    <div
      ref={container}
      onScroll={onScroll}
      className="min-h-0 flex-1 overflow-y-auto px-4 py-6"
    >
      <ol className="mx-auto flex w-full max-w-3xl flex-col gap-6">
        {visibleMessages.map((message, index) => (
          <li key={message.id}>
            <Message
              message={message}
              citations={citationsByMessageId[message.id] ?? []}
              isStreamingLast={waiting && index === visibleMessages.length - 1}
            />
          </li>
        ))}
      </ol>
    </div>
  )
}
