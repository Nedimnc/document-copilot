import { useCallback, useEffect, useState } from "react"
import { Outlet, useNavigate, useParams } from "react-router-dom"

import { AppSidebar } from "@/components/layout/AppSidebar"
import { Separator } from "@/components/ui/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { createThread, deleteThread, listThreads } from "@/lib/api"
import { signOut } from "@/lib/auth"
import type { ChatThread } from "@/lib/chat"
import { supabase } from "@/lib/supabase"

export type ChatOutletContext = {
  refreshThreads: () => Promise<void>
  newChat: () => void
  creating: boolean
}

export function ChatLayout() {
  const navigate = useNavigate()
  const { threadId } = useParams<{ threadId: string }>()
  const [threads, setThreads] = useState<ChatThread[]>([])
  const [email, setEmail] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const refreshThreads = useCallback(async () => {
    try {
      setThreads(await listThreads())
      setError(null)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load threads")
    }
  }, [])

  useEffect(() => {
    void refreshThreads()
  }, [refreshThreads])

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => {
      setEmail(data.user?.email ?? null)
    })
  }, [])

  async function onCreate() {
    setCreating(true)
    try {
      const thread = await createThread()
      await refreshThreads()
      navigate(`/chats/${thread.id}`)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not create a thread")
    } finally {
      setCreating(false)
    }
  }

  async function onDelete(thread: ChatThread): Promise<boolean> {
    setDeleting(true)
    try {
      await deleteThread(thread.id)
      await refreshThreads()
      if (threadId === thread.id) {
        navigate("/")
      }
      return true
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not delete that chat")
      return false
    } finally {
      setDeleting(false)
    }
  }

  const activeThread = threads.find((thread) => thread.id === threadId)
  const heading = activeThread?.title?.trim() || "Conversations"

  return (
    // Lock the shell to the viewport so the message list scrolls internally and
    // the composer stays pinned — otherwise the page itself grows and the input
    // slides below the fold while an answer streams in.
    <SidebarProvider className="h-svh overflow-hidden">
      <AppSidebar
        threads={threads}
        email={email}
        creating={creating}
        deleting={deleting}
        activeThreadId={threadId}
        onCreate={() => {
          void onCreate()
        }}
        onDelete={onDelete}
        onSignOut={() => {
          void signOut()
        }}
      />
      <SidebarInset className="min-h-0">
        <header className="flex h-12 shrink-0 items-center gap-2 border-b px-3">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-1 data-[orientation=vertical]:h-4" />
          <span className="truncate text-sm font-medium">{heading}</span>
        </header>
        {error ? (
          <p
            className="border-b border-destructive/30 bg-destructive/10 px-4 py-2 text-sm text-destructive"
            role="alert"
          >
            {error}
          </p>
        ) : null}
        <Outlet
          context={
            {
              refreshThreads,
              creating,
              newChat: () => {
                void onCreate()
              },
            } satisfies ChatOutletContext
          }
        />
      </SidebarInset>
    </SidebarProvider>
  )
}
