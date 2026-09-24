import { ExternalLink } from "lucide-react"
import { createContext, useContext, useState, type ReactNode } from "react"

import { FilingBadge } from "@/components/primitives/FilingBadge"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { CitationExcerpt } from "@/components/chat/CitationExcerpt"
import type { MessageCitation } from "@/lib/citations"

type ActiveCitation = { citation: MessageCitation; index?: number }
type CitationPanelValue = { open: (citation: MessageCitation, index?: number) => void }

const CitationPanelContext = createContext<CitationPanelValue | null>(null)

export function useCitationPanel(): CitationPanelValue {
  const value = useContext(CitationPanelContext)
  if (!value) {
    throw new Error("useCitationPanel must be used within a CitationPanelProvider")
  }
  return value
}

function formatFilingDate(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) {
    return iso
  }
  return new Intl.DateTimeFormat("en-US", { dateStyle: "long" }).format(date)
}

// One panel is shared by every citation in the thread. Clicking an inline [n]
// marker or a source row opens the filing here rather than punting to a new tab;
// the new tab is available as a secondary action inside the panel.
export function CitationPanelProvider({ children }: { children: ReactNode }) {
  const [active, setActive] = useState<ActiveCitation | null>(null)

  return (
    <CitationPanelContext.Provider
      value={{ open: (citation, index) => setActive({ citation, index }) }}
    >
      {children}
      <Sheet
        open={active !== null}
        onOpenChange={(next) => {
          if (!next) setActive(null)
        }}
      >
        <SheetContent side="right" className="w-full gap-0 p-0 sm:max-w-lg">
          {active ? (
            <>
              <SheetHeader className="border-b pr-12">
                <SheetTitle className="flex items-center gap-2">
                  {active.index != null ? (
                    <span className="font-semibold text-link">[{active.index}]</span>
                  ) : null}
                  <FilingBadge citation={active.citation} className="text-sm" />
                </SheetTitle>
                <SheetDescription>
                  {active.citation.company_name}, filed{" "}
                  {formatFilingDate(active.citation.filing_date)}
                  {active.citation.page != null ? ` · page ${active.citation.page}` : ""}
                </SheetDescription>
              </SheetHeader>

              <div className="min-h-0 flex-1 overflow-y-auto p-4">
                {active.citation.section ? (
                  <div className="mb-4">
                    <p className="text-xs font-medium text-muted-foreground">Section</p>
                    <p className="mt-1 text-sm">{active.citation.section}</p>
                  </div>
                ) : null}
                <p className="text-xs font-medium text-muted-foreground">Cited passage</p>
                <div className="mt-2">
                  <CitationExcerpt excerpt={active.citation.excerpt} />
                </div>
              </div>

              <SheetFooter className="border-t">
                <Button asChild variant="outline">
                  <a
                    href={active.citation.source_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <ExternalLink className="size-4" />
                    Open on SEC.gov
                  </a>
                </Button>
              </SheetFooter>
            </>
          ) : null}
        </SheetContent>
      </Sheet>
    </CitationPanelContext.Provider>
  )
}
