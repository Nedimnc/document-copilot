import { useChat } from "@ai-sdk/react"
import { DefaultChatTransport, type UIMessage } from "ai"
import { useEffect, useMemo, useState } from "react"
import { useOutletContext, useParams } from "react-router-dom"

import { Composer } from "@/components/chat/Composer"
import { MessageList } from "@/components/chat/MessageList"
import { listMessages } from "@/lib/api"
import { getAccessToken } from "@/lib/auth"
import { toUIMessage } from "@/lib/chat"
import { env } from "@/lib/env"
import { ApiError } from "@/lib/http"
import type { ChatOutletContext } from "@/pages/chat/ChatLayout"

export function ChatPage() {
  const { threadId } = useParams<{ threadId: string }>()
  if (!threadId) {
    return null
  }
  return <ThreadLoader key={threadId} threadId={threadId} />
}

function ThreadLoader({ threadId }: { threadId: string }) {
  const [initialMessages, setInitialMessages] = useState<UIMessage[] | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    listMessages(threadId)
      .then((messages) => {
        if (!cancelled) {
          setInitialMessages(messages.map(toUIMessage))
        }
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return
        }
        if (error instanceof ApiError && error.status === 403) {
          setLoadError("You do not have access to this conversation.")
          return
        }
        if (error instanceof ApiError && error.status === 404) {
          setLoadError("This conversation was not found.")
          return
        }
        setLoadError(error instanceof Error ? error.message : "Could not load messages")
      })
    return () => {
      cancelled = true
    }
  }, [threadId])

  if (loadError) {
    return (
      <main className="flex flex-1 items-center justify-center px-6 text-sm text-red-700">
        {loadError}
      </main>
    )
  }

  if (initialMessages === null) {
    return (
      <main className="flex flex-1 items-center justify-center text-sm text-zinc-500">
        Loading conversation…
      </main>
    )
  }

  return (
    <ChatWindow
      key={threadId}
      threadId={threadId}
      initialMessages={initialMessages}
    />
  )
}

function ChatWindow({
  threadId,
  initialMessages,
}: {
  threadId: string
  initialMessages: UIMessage[]
}) {
  const { refreshThreads } = useOutletContext<ChatOutletContext>()
  const transport = useMemo(
    () =>
      new DefaultChatTransport({
        api: `${env.apiBaseUrl}/chat/stream`,
        headers: async () => {
          const token = await getAccessToken()
          return token ? { Authorization: `Bearer ${token}` } : {}
        },
      }),
    [],
  )

  const { messages, sendMessage, status, error } = useChat({
    id: threadId,
    messages: initialMessages,
    transport,
  })

  useEffect(() => {
    if (status === "ready" && messages.length > initialMessages.length) {
      void refreshThreads()
    }
  }, [initialMessages.length, messages.length, refreshThreads, status])

  return (
    <main className="flex min-h-0 flex-1 flex-col">
      <MessageList messages={messages} status={status} />
      {error ? (
        <p className="px-4 text-sm text-red-700" role="alert">
          {error.message}
        </p>
      ) : null}
      <Composer
        disabled={status === "submitted" || status === "streaming"}
        onSend={async (text) => {
          await sendMessage({ text })
        }}
      />
    </main>
  )
}
