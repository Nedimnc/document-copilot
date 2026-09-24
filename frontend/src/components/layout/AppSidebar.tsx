import { FileText, Plus } from "lucide-react"
import { useState } from "react"

import { ThreadItem } from "@/components/layout/ThreadItem"
import { UserMenu } from "@/components/layout/UserMenu"
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Button } from "@/components/ui/button"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar"
import { threadLabel, type ChatThread } from "@/lib/chat"
import { groupThreads } from "@/lib/threadGroups"

export function AppSidebar({
  threads,
  email,
  creating,
  deleting,
  activeThreadId,
  onCreate,
  onDelete,
  onSignOut,
}: {
  threads: ChatThread[]
  email: string | null
  creating: boolean
  deleting: boolean
  activeThreadId?: string
  onCreate: () => void
  onDelete: (thread: ChatThread) => Promise<boolean>
  onSignOut: () => void
}) {
  const { setOpenMobile, isMobile } = useSidebar()
  const groups = groupThreads(threads)
  const [pending, setPending] = useState<ChatThread | null>(null)

  // On mobile the sidebar is an overlay — close it once the analyst picks a thread.
  function closeOnMobile() {
    if (isMobile) {
      setOpenMobile(false)
    }
  }

  return (
    <Sidebar collapsible="offcanvas">
      <SidebarHeader className="gap-3">
        <div className="flex items-center gap-2 px-1 pt-1">
          <div className="flex size-7 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <FileText className="size-4" />
          </div>
          <div className="grid text-sm leading-tight">
            <span className="font-semibold">Document Copilot</span>
            <span className="text-xs text-muted-foreground">Filing research</span>
          </div>
        </div>
        <Button
          variant="outline"
          className="w-full justify-start"
          disabled={creating}
          onClick={onCreate}
        >
          <Plus className="size-4" />
          {creating ? "Creating…" : "New chat"}
        </Button>
      </SidebarHeader>

      <SidebarContent>
        {groups.length === 0 ? (
          <div className="px-4 py-6 text-sm text-muted-foreground">
            No conversations yet. Start one to see it here.
          </div>
        ) : (
          groups.map((group) => (
            <SidebarGroup key={group.label}>
              <SidebarGroupLabel>{group.label}</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {group.threads.map((thread) => (
                    <ThreadItem
                      key={thread.id}
                      thread={thread}
                      isActive={thread.id === activeThreadId}
                      disabled={deleting}
                      onSelect={closeOnMobile}
                      onDelete={() => setPending(thread)}
                    />
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          ))
        )}
      </SidebarContent>

      <SidebarFooter>
        <UserMenu email={email} onSignOut={onSignOut} />
      </SidebarFooter>
      <SidebarRail />

      <AlertDialog
        open={pending !== null}
        onOpenChange={(open) => {
          if (!open && !deleting) {
            setPending(null)
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this chat?</AlertDialogTitle>
            <AlertDialogDescription>
              {pending
                ? `“${threadLabel(pending)}” and its messages will be permanently removed.`
                : "This chat and its messages will be permanently removed."}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <Button
              variant="destructive"
              disabled={deleting || pending === null}
              onClick={() => {
                if (!pending) {
                  return
                }
                void onDelete(pending).then((ok) => {
                  if (ok) {
                    setPending(null)
                  }
                })
              }}
            >
              {deleting ? "Deleting…" : "Delete"}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Sidebar>
  )
}
