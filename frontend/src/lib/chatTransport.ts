import { DefaultChatTransport, type UIMessage } from "ai"

import { getAccessToken } from "@/lib/auth"
import { env } from "@/lib/env"

export type PipelineStatus = {
  phase: string
  label: string
}

type StatusListener = (status: PipelineStatus | null) => void

function parseStatusLine(line: string): PipelineStatus | null {
  if (!line.startsWith("data: ") || line === "data: [DONE]") {
    return null
  }
  try {
    const payload = JSON.parse(line.slice(6)) as {
      type?: string
      data?: PipelineStatus
    }
    if (payload.type === "data-copilot-status" && payload.data?.label) {
      return payload.data
    }
  } catch {
    return null
  }
  return null
}

function wrapStreamWithStatus(
  body: ReadableStream<Uint8Array>,
  onStatus: StatusListener,
): ReadableStream<Uint8Array> {
  const decoder = new TextDecoder()
  const encoder = new TextEncoder()
  let buffer = ""

  return body.pipeThrough(
    new TransformStream<Uint8Array, Uint8Array>({
      transform(chunk, controller) {
        buffer += decoder.decode(chunk, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() ?? ""
        for (const line of lines) {
          const status = parseStatusLine(line.trim())
          if (status) {
            onStatus(status.phase === "done" ? null : status)
          }
        }
        controller.enqueue(chunk)
      },
      flush(controller) {
        if (buffer.trim()) {
          const status = parseStatusLine(buffer.trim())
          if (status) {
            onStatus(status.phase === "done" ? null : status)
          }
        }
        controller.enqueue(encoder.encode(""))
      },
    }),
  )
}

export function createChatTransport(onStatus: StatusListener) {
  return new DefaultChatTransport({
    api: `${env.apiBaseUrl}/chat/stream`,
    headers: async (): Promise<Record<string, string>> => {
      const token = await getAccessToken()
      return token ? { Authorization: `Bearer ${token}` } : {}
    },
    fetch: async (input, init) => {
      onStatus({ phase: "sending", label: "Sending question…" })
      const response = await fetch(input, init)
      if (!response.ok || !response.body) {
        onStatus(null)
        return response
      }
      return new Response(wrapStreamWithStatus(response.body, onStatus), {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
      })
    },
  })
}

export type { UIMessage }
