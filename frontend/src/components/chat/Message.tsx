import { Bot } from "lucide-react"
import type { UIMessage } from "ai"
import { useMemo } from "react"

import { CitationList } from "@/components/chat/CitationList"
import { useCitationPanel } from "@/components/chat/CitationPanel"
import { Markdown } from "@/components/chat/Markdown"
import { CopyButton } from "@/components/primitives/CopyButton"
import type { MessageCitation } from "@/lib/citations"
import { messageText } from "@/lib/chat"

// Conservative: only treat a whole answer as a refusal when it cites nothing and
// reads like an explicit "no evidence" reply. Partial refusals stay inline.
const REFUSAL =
  /not enough evidence|no evidence|does not (support|contain|provide)|cannot (find|answer|confirm|determine)|insufficient (evidence|information)/i

function isRefusal(text: string, citationCount: number): boolean {
  return citationCount === 0 && text.trim().length < 500 && REFUSAL.test(text)
}

function TypingDots() {
  return (
    <div className="flex items-center gap-1 py-1" aria-label="Assistant is responding">
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          className="size-1.5 animate-bounce rounded-full bg-muted-foreground/60"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </div>
  )
}

export function Message({
  message,
  citations,
  isStreamingLast,
}: {
  message: UIMessage
  citations: MessageCitation[]
  isStreamingLast: boolean
}) {
  const text = messageText(message)
  const { open: openCitation } = useCitationPanel()
  // Same ordering the source list and inline [n] markers use, so marker N always
  // resolves to the same filing.
  const ordered = useMemo(
    () => [...citations].sort((a, b) => a.sort_order - b.sort_order),
    [citations],
  )

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-sm bg-muted px-4 py-2.5 text-sm whitespace-pre-wrap">
          {text}
        </div>
      </div>
    )
  }

  const waitingForFirstToken = isStreamingLast && !text.trim()
  const refusal = isRefusal(text, citations.length)

  return (
    <div className="group flex gap-3">
      <div className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-md border bg-card text-muted-foreground">
        <Bot className="size-4" />
      </div>
      <div className="min-w-0 flex-1">
        {waitingForFirstToken ? (
          <TypingDots />
        ) : refusal ? (
          <div className="rounded-lg border border-refusal-border bg-refusal px-3 py-2 text-sm text-refusal-foreground">
            {text}
          </div>
        ) : (
          <Markdown
            content={text}
            citationCount={ordered.length}
            onCitationClick={(n) => {
              const citation = ordered[n - 1]
              if (citation) openCitation(citation, n)
            }}
          />
        )}

        <CitationList citations={citations} />

        {!waitingForFirstToken && text.trim() ? (
          <div className="mt-1.5 flex opacity-0 transition-opacity group-focus-within:opacity-100 group-hover:opacity-100">
            <CopyButton text={text} label="Copy answer" />
          </div>
        ) : null}
      </div>
    </div>
  )
}
