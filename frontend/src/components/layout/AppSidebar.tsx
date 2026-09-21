import { FileText, Plus } from "lucide-react"
import { NavLink } from "react-router-dom"

import { UserMenu } from "@/components/layout/UserMenu"
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
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar"
import type { ChatThread } from "@/lib/chat"
import { groupThreads } from "@/lib/threadGroups"

function threadLabel(thread: ChatThread): string {
  return thread.title?.trim() || "New chat"
}

export function AppSidebar({
  threads,
  email,
  creating,
  activeThreadId,
  onCreate,
  onSignOut,
}: {
  threads: ChatThread[]
  email: string | null
  creating: boolean
  activeThreadId?: string
  onCreate: () => void
  onSignOut: () => void
}) {
  const { setOpenMobile, isMobile } = useSidebar()
  const groups = groupThreads(threads)

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
                    <SidebarMenuItem key={thread.id}>
                      <SidebarMenuButton
                        asChild
                        isActive={thread.id === activeThreadId}
                        tooltip={threadLabel(thread)}
                      >
                        <NavLink to={`/chats/${thread.id}`} onClick={closeOnMobile}>
                          <span className="truncate">{threadLabel(thread)}</span>
                        </NavLink>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
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
    </Sidebar>
  )
}
