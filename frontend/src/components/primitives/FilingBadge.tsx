import type { MessageCitation } from "@/lib/citations"
import { cn } from "@/lib/utils"

// Ticker + filing identity, with figures in tabular-nums so years/pages align
// when several citations stack. Deliberately no middle-dot meta string.
export function FilingBadge({
  citation,
  className,
}: {
  citation: MessageCitation
  className?: string
}) {
  return (
    <span className={cn("inline-flex items-baseline gap-1.5 tabular-nums", className)}>
      <span className="font-semibold">{citation.ticker}</span>
      <span className="text-muted-foreground">
        {citation.filing_type} FY{citation.fiscal_year}
      </span>
      {citation.page != null ? (
        <span className="text-muted-foreground">p.&nbsp;{citation.page}</span>
      ) : null}
    </span>
  )
}
