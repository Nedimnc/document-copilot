import { Loader2 } from "lucide-react"

import type { PipelineStatus } from "@/lib/chatTransport"

export function PipelineStatusBar({ status }: { status: PipelineStatus | null }) {
  if (!status) {
    return null
  }

  return (
    <div className="px-4">
      <div
        className="mx-auto flex w-full max-w-3xl items-center gap-2 py-2 text-sm text-muted-foreground"
        role="status"
        aria-live="polite"
      >
        <Loader2 className="size-3.5 animate-spin" aria-hidden />
        <span>{status.label}</span>
      </div>
    </div>
  )
}
