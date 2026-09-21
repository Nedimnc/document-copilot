import { useChat } from "@ai-sdk/react"
import type { UIMessage } from "ai"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { useOutletContext, useParams } from "react-router-dom"

import { CitationPanelProvider } from "@/components/chat/CitationPanel"
import { Composer } from "@/components/chat/Composer"
import { EmptyState } from "@/components/chat/EmptyState"
import { MessageList } from "@/components/chat/MessageList"
import { PipelineStatusBar } from "@/components/chat/PipelineStatus"
import { Skeleton } from "@/components/ui/skeleton"
import { listMessages } from "@/lib/api"
import type { MessageCitation } from "@/lib/citations"
import { citationsFromMessages, toUIMessage, visibleChatMessages } from "@/lib/chat"
import { createChatTransport, type PipelineStatus } from "@/lib/chatTransport"
import { ApiError } from "@/lib/http"
import type { ChatOutletContext } from "@/pages/chat/ChatLayout"

export function ChatPage() {
  const { threadId } = useParams<{ threadId: string }>()
  if (!threadId) {
    return null
  }
  return <ThreadLoader key={threadId} threadId={threadId} />
}

function LoadingSkeleton() {
  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-6">
        <div className="flex justify-end">
          <Skeleton className="h-10 w-64 rounded-2xl" />
        </div>
        <div className="flex gap-3">
          <Skeleton className="size-7 shrink-0 rounded-md" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        </div>
      </div>
    </div>
  )
}

function ThreadLoader({ threadId }: { threadId: string }) {
  const [initialMessages, setInitialMessages] = useState<UIMessage[] | null>(null)
  const [initialCitations, setInitialCitations] = useState<
    Record<string, MessageCitation[]>
  >({})
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    listMessages(threadId)
      .then((messages) => {
        if (!cancelled) {
          setInitialMessages(messages.map(toUIMessage))
          setInitialCitations(citationsFromMessages(messages))
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
      <div className="flex flex-1 items-center justify-center px-6 text-center text-sm text-muted-foreground">
        {loadError}
      </div>
    )
  }

  if (initialMessages === null) {
    return <LoadingSkeleton />
  }

  return (
    <ChatWindow
      key={threadId}
      threadId={threadId}
      initialMessages={initialMessages}
      initialCitations={initialCitations}
    />
  )
}

function ChatWindow({
  threadId,
  initialMessages,
  initialCitations,
}: {
  threadId: string
  initialMessages: UIMessage[]
  initialCitations: Record<string, MessageCitation[]>
}) {
  const { refreshThreads } = useOutletContext<ChatOutletContext>()
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus | null>(null)
  const [citationsByMessageId, setCitationsByMessageId] =
    useState<Record<string, MessageCitation[]>>(initialCitations)

  const transport = useMemo(() => createChatTransport(setPipelineStatus), [])

  const { messages, sendMessage, setMessages, status, error, stop } = useChat({
    id: threadId,
    messages: initialMessages,
    transport,
  })

  const syncFromServer = useCallback(async () => {
    const stored = await listMessages(threadId)
    setMessages(stored.map(toUIMessage))
    setCitationsByMessageId(citationsFromMessages(stored))
  }, [threadId, setMessages])

  const prevStatus = useRef(status)

  useEffect(() => {
    setCitationsByMessageId(initialCitations)
  }, [initialCitations, threadId])

  useEffect(() => {
    const streamEnded = prevStatus.current !== "ready" && status === "ready"
    prevStatus.current = status

    if (status === "ready") {
      setPipelineStatus(null)
    }

    if (!streamEnded) {
      return
    }

    void syncFromServer()
    void refreshThreads()
  }, [refreshThreads, status, syncFromServer])

  const busy = status === "submitted" || status === "streaming"
  const isEmpty = visibleChatMessages(messages, status).length === 0

  return (
    <CitationPanelProvider>
      <div className="flex min-h-0 flex-1 flex-col">
        {isEmpty && !busy ? (
        <EmptyState onPick={(question) => void sendMessage({ text: question })} />
      ) : (
        <MessageList
          messages={messages}
          status={status}
          citationsByMessageId={citationsByMessageId}
        />
      )}

      <PipelineStatusBar
        status={
          pipelineStatus ??
          (status === "submitted"
            ? { phase: "waiting", label: "Waiting for response…" }
            : null)
        }
      />

      {error ? (
        <div className="px-4">
          <p
            className="mx-auto w-full max-w-3xl text-sm text-destructive"
            role="alert"
          >
            {error.message}
          </p>
        </div>
      ) : null}

      <Composer
        busy={busy}
        onStop={stop}
        onSend={async (text) => {
          await sendMessage({ text })
        }}
      />
      </div>
    </CitationPanelProvider>
  )
}
