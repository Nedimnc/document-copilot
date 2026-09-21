import { ChevronDown, ChevronRight } from "lucide-react"
import { useState } from "react"

import { useCitationPanel } from "@/components/chat/CitationPanel"
import { FilingBadge } from "@/components/primitives/FilingBadge"
import type { MessageCitation } from "@/lib/citations"

export function CitationList({ citations }: { citations: MessageCitation[] }) {
  const [open, setOpen] = useState(false)
  const { open: openCitation } = useCitationPanel()

  const ordered = [...citations].sort((a, b) => a.sort_order - b.sort_order)

  if (ordered.length === 0) {
    return null
  }

  return (
    <section aria-label="Sources" className="mt-3">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="inline-flex items-center gap-1.5 rounded-md border bg-card px-2.5 py-1 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:outline-none"
      >
        <ChevronDown className={`size-3.5 transition-transform ${open ? "rotate-180" : ""}`} />
        {open ? "Hide sources" : `Sources (${ordered.length})`}
      </button>

      {open ? (
        <ol className="mt-2 flex flex-col gap-1.5">
          {ordered.map((citation, i) => (
            <li key={citation.id}>
              <button
                type="button"
                onClick={() => openCitation(citation, i + 1)}
                className="flex w-full items-center gap-2 rounded-lg border bg-card px-3 py-2 text-left text-xs transition-colors hover:border-foreground/20 hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:outline-none"
              >
                <span className="font-semibold text-link">[{i + 1}]</span>
                <FilingBadge citation={citation} className="text-xs" />
                {citation.section ? (
                  <span className="min-w-0 flex-1 truncate text-muted-foreground">
                    {citation.section}
                  </span>
                ) : (
                  <span className="flex-1" />
                )}
                <ChevronRight className="size-3.5 shrink-0 text-muted-foreground" />
              </button>
            </li>
          ))}
        </ol>
      ) : null}
    </section>
  )
}
