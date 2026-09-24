import type { UIMessage } from "ai"

import type { MessageCitation } from "@/lib/citations"

export type ChatThread = {
  id: string
  title: string | null
  created_at: string
  updated_at: string
}

export function threadLabel(thread: ChatThread): string {
  return thread.title?.trim() || "New chat"
}

export type StoredChatMessage = {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  parts: { type: "text"; text: string }[]
  citations?: MessageCitation[]
  created_at: string
}

export function toUIMessage(message: StoredChatMessage): UIMessage {
  const role = message.role === "assistant" ? "assistant" : "user"
  const parts =
    message.parts.length > 0
      ? message.parts
      : [{ type: "text" as const, text: message.content }]
  return { id: message.id, role, parts }
}

export function messageText(message: UIMessage): string {
  return message.parts
    .filter((part): part is { type: "text"; text: string } => part.type === "text")
    .map((part) => part.text)
    .join("")
}

export type ChatStatus = "submitted" | "streaming" | "ready" | "error"

/** Drop empty assistant placeholders left over from the AI SDK stream lifecycle. */
export function visibleChatMessages(
  messages: UIMessage[],
  status: ChatStatus,
): UIMessage[] {
  const waiting = status === "submitted" || status === "streaming"
  return messages.filter((message, index) => {
    if (message.role !== "assistant") {
      return true
    }
    if (messageText(message).trim()) {
      return true
    }
    const isLast = index === messages.length - 1
    return waiting && isLast
  })
}

export function citationsFromMessages(
  messages: StoredChatMessage[],
): Record<string, MessageCitation[]> {
  const map: Record<string, MessageCitation[]> = {}
  for (const message of messages) {
    if (message.citations && message.citations.length > 0) {
      map[message.id] = message.citations
    }
  }
  return map
}
