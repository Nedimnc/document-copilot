import { useCallback, useEffect, useState } from "react"
import { Outlet, useNavigate } from "react-router-dom"

import { ThreadSidebar } from "@/components/chat/ThreadSidebar"
import { createThread, listThreads } from "@/lib/api"
import { signOut } from "@/lib/auth"
import type { ChatThread } from "@/lib/chat"
import { supabase } from "@/lib/supabase"

export type ChatOutletContext = {
  refreshThreads: () => Promise<void>
}

export function ChatLayout() {
  const navigate = useNavigate()
  const [threads, setThreads] = useState<ChatThread[]>([])
  const [email, setEmail] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)

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

  return (
    <div className="flex min-h-svh">
      <ThreadSidebar
        threads={threads}
        email={email}
        creating={creating}
        onCreate={() => {
          void onCreate()
        }}
        onSignOut={() => {
          void signOut()
        }}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        {error ? (
          <p className="border-b border-red-200 bg-red-50 px-4 py-2 text-sm text-red-700">
            {error}
          </p>
        ) : null}
        <Outlet context={{ refreshThreads } satisfies ChatOutletContext} />
      </div>
    </div>
  )
}
