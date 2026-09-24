import type { ChatThread, StoredChatMessage } from "@/lib/chat"
import { request } from "@/lib/http"

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  put: <T>(path: string, body?: unknown) => request<T>("PUT", path, body),
  patch: <T>(path: string, body?: unknown) => request<T>("PATCH", path, body),
  delete: <T>(path: string) => request<T>("DELETE", path),
}

export function listThreads() {
  return api.get<ChatThread[]>("/chat/threads")
}

export function createThread(title?: string) {
  return api.post<ChatThread>("/chat/threads", { title })
}

export function deleteThread(threadId: string) {
  return api.delete<void>(`/chat/threads/${threadId}`)
}

export function listMessages(threadId: string) {
  return api.get<StoredChatMessage[]>(`/chat/threads/${threadId}/messages`)
}
