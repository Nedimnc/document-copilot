import { ChevronDown, TriangleAlert } from "lucide-react"
import { useState } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import { formatCitationExcerpt } from "@/lib/formatCitationExcerpt"

function MarkdownExcerpt({ text }: { text: string }) {
  return (
    <div className="text-sm leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          table: ({ children }) => (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-xs tabular-nums">{children}</table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="border-b bg-muted/50">{children}</thead>
          ),
          tr: ({ children }) => (
            <tr className="border-b border-border/60 last:border-0">{children}</tr>
          ),
          th: ({ children }) => (
            <th className="px-2.5 py-1.5 text-left font-medium">{children}</th>
          ),
          td: ({ children }) => <td className="px-2.5 py-1.5 align-top">{children}</td>,
          p: ({ children }) => <p className="my-2 first:mt-0 last:mb-0">{children}</p>,
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  )
}

/** Shared collapsible "Show raw extract" disclosure. */
function RawExtractToggle({ raw }: { raw: string }) {
  const [showRaw, setShowRaw] = useState(false)

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={() => setShowRaw((v) => !v)}
        aria-expanded={showRaw}
        className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground"
      >
        <ChevronDown className={`size-3 transition-transform ${showRaw ? "rotate-180" : ""}`} />
        {showRaw ? "Hide raw extract" : "Show raw extract"}
      </button>

      {showRaw ? (
        <p className="rounded-md bg-muted p-2 font-mono text-[11px] leading-relaxed break-words text-muted-foreground">
          {raw}
        </p>
      ) : null}
    </div>
  )
}

// The excerpt held readable narrative plus some shredded table numbers. We show the
// prose we could recover and flag that stray table values were dropped.
function PartialExcerpt({ text, raw }: { text: string; raw: string }) {
  return (
    <div className="space-y-3">
      <p className="text-sm leading-relaxed whitespace-pre-wrap">{text}</p>
      <div className="flex gap-2 rounded-md border border-refusal-border bg-refusal px-3 py-2 text-xs text-refusal-foreground">
        <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />
        <p>
          Some table values from this passage were dropped because their row and column
          labels were lost when the document was processed. Open the filing on SEC.gov to
          read those numbers in context.
        </p>
      </div>
      <RawExtractToggle raw={raw} />
    </div>
  )
}

// The stored text is a filing table that lost its row/column headers at ingest.
// Don't fake a structured table — say so plainly and point to the source.
function GarbledTableNotice({ raw }: { raw: string }) {
  return (
    <div className="space-y-2">
      <div className="flex gap-2 rounded-md border border-refusal-border bg-refusal px-3 py-2 text-xs text-refusal-foreground">
        <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />
        <p>
          This citation points at a table in the filing, but the stored text lost its
          row and column labels when the document was processed, so the numbers below
          aren't reliably labeled. Open the filing on SEC.gov to read the table in
          context.
        </p>
      </div>
      <RawExtractToggle raw={raw} />
    </div>
  )
}

export function CitationExcerpt({ excerpt }: { excerpt: string }) {
  const formatted = formatCitationExcerpt(excerpt)

  if (formatted.kind === "prose") {
    if (!formatted.text) {
      return <p className="text-sm text-muted-foreground">No passage text stored for this cite.</p>
    }
    return <p className="text-sm leading-relaxed whitespace-pre-wrap">{formatted.text}</p>
  }

  if (formatted.kind === "markdown") {
    return <MarkdownExcerpt text={formatted.text} />
  }

  if (formatted.kind === "partial") {
    return <PartialExcerpt text={formatted.text} raw={formatted.raw} />
  }

  return <GarbledTableNotice raw={formatted.raw} />
}
