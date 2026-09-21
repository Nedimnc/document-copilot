import { FileText } from "lucide-react"

const SUGGESTIONS = [
  "Across Apple's 2021–2025 10-Ks, how did the revenue mix between iPhone, Services, Mac, iPad, and Wearables change?",
  "Compare AWS operating income and margin against North America and International from 2021–2025.",
  "How did NVIDIA describe Data Center demand drivers, customer concentration, and supply constraints from FY2021–FY2025?",
  "Which companies materially changed AI or export-control risk-factor language between 2021 and 2025?",
]

export function EmptyState({ onPick }: { onPick: (question: string) => void }) {
  return (
    <div className="flex flex-1 items-center justify-center overflow-y-auto px-4 py-10">
      <div className="w-full max-w-2xl text-center">
        <div className="mx-auto flex size-11 items-center justify-center rounded-lg border bg-card">
          <FileText className="size-5 text-muted-foreground" />
        </div>
        <h2 className="mt-4 text-lg font-semibold">Ask the filings, get a cited answer</h2>
        <p className="mx-auto mt-1 max-w-md text-sm text-muted-foreground">
          Every answer is drawn from the SEC 10-K corpus and cites the exact filing and
          page. If the filings don't support it, the copilot says so.
        </p>

        <div className="mt-6 grid gap-2 text-left sm:grid-cols-2">
          {SUGGESTIONS.map((question) => (
            <button
              key={question}
              type="button"
              onClick={() => onPick(question)}
              className="rounded-lg border bg-card p-3 text-sm text-muted-foreground transition-colors hover:border-foreground/20 hover:bg-muted hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:outline-none"
            >
              {question}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
