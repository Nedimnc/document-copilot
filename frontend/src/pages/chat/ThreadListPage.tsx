import { Plus } from "lucide-react"
import { useOutletContext } from "react-router-dom"

import { Button } from "@/components/ui/button"
import type { ChatOutletContext } from "@/pages/chat/ChatLayout"

export function ThreadListPage() {
  const { newChat, creating } = useOutletContext<ChatOutletContext>()

  return (
    <div className="flex flex-1 items-center justify-center px-6 py-10 text-center">
      <div className="max-w-md">
        <h1 className="text-xl font-semibold">Document Copilot</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Ask questions about the SEC 10-K corpus and get answers cited to the exact
          filing and page. Pick a past conversation from the sidebar, or start a new one.
        </p>
        <Button className="mt-5" disabled={creating} onClick={newChat}>
          <Plus className="size-4" />
          {creating ? "Creating…" : "New chat"}
        </Button>
      </div>
    </div>
  )
}
