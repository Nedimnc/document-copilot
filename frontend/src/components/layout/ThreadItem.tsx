import { Trash2 } from "lucide-react"
import { NavLink } from "react-router-dom"

import {
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { threadLabel, type ChatThread } from "@/lib/chat"

export function ThreadItem({
  thread,
  isActive,
  disabled,
  onSelect,
  onDelete,
}: {
  thread: ChatThread
  isActive: boolean
  disabled: boolean
  onSelect: () => void
  onDelete: () => void
}) {
  const label = threadLabel(thread)

  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild isActive={isActive} tooltip={label}>
        <NavLink to={`/chats/${thread.id}`} onClick={onSelect} className="pr-7">
          <span className="truncate">{label}</span>
        </NavLink>
      </SidebarMenuButton>
      <SidebarMenuAction
        showOnHover
        disabled={disabled}
        aria-label={`Delete ${label}`}
        title="Delete chat"
        className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
        onClick={(event) => {
          event.preventDefault()
          event.stopPropagation()
          onDelete()
        }}
      >
        <Trash2 />
      </SidebarMenuAction>
    </SidebarMenuItem>
  )
}
