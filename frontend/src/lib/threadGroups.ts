import type { ChatThread } from "@/lib/chat"

export type ThreadGroup = {
  label: string
  threads: ChatThread[]
}

// Midnight-aligned day difference so "Yesterday" means the previous calendar
// day, not "24h ago" — analysts think in calendar days, not rolling windows.
function daysAgo(iso: string, now: Date): number {
  const then = new Date(iso)
  const startOfThen = new Date(then.getFullYear(), then.getMonth(), then.getDate())
  const startOfNow = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const msPerDay = 24 * 60 * 60 * 1000
  return Math.round((startOfNow.getTime() - startOfThen.getTime()) / msPerDay)
}

function bucketFor(days: number): string {
  if (days <= 0) return "Today"
  if (days === 1) return "Yesterday"
  if (days <= 7) return "Previous 7 days"
  if (days <= 30) return "Previous 30 days"
  return "Older"
}

const ORDER = ["Today", "Yesterday", "Previous 7 days", "Previous 30 days", "Older"]

/** Group threads into recency buckets, newest first, using `updated_at`. */
export function groupThreads(threads: ChatThread[], now = new Date()): ThreadGroup[] {
  const byLabel = new Map<string, ChatThread[]>()

  const sorted = [...threads].sort(
    (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
  )

  for (const thread of sorted) {
    const label = bucketFor(daysAgo(thread.updated_at, now))
    const existing = byLabel.get(label)
    if (existing) {
      existing.push(thread)
    } else {
      byLabel.set(label, [thread])
    }
  }

  return ORDER.filter((label) => byLabel.has(label)).map((label) => ({
    label,
    threads: byLabel.get(label)!,
  }))
}
