import type { UIMessage } from "ai"

export type ChatThread = {
  id: string
  title: string | null
  created_at: string
  updated_at: string
}

export type StoredChatMessage = {
  id: string
  role: "user" | "assistant" | "system"
  content: string
  parts: { type: "text"; text: string }[]
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
