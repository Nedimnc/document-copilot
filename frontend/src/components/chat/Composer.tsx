import { ArrowUp, Square } from "lucide-react"
import { useRef, useState, type FormEvent } from "react"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

const MAX_HEIGHT = 200

export function Composer({
  busy,
  onSend,
  onStop,
}: {
  busy: boolean
  onSend: (text: string) => Promise<void>
  onStop: () => void
}) {
  const [text, setText] = useState("")
  const ref = useRef<HTMLTextAreaElement>(null)

  function resize() {
    const el = ref.current
    if (!el) return
    el.style.height = "auto"
    el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT)}px`
  }

  async function submit() {
    const next = text.trim()
    if (!next || busy) {
      return
    }
    setText("")
    // Reset height after clearing so the box snaps back to one row.
    requestAnimationFrame(resize)
    try {
      await onSend(next)
    } catch {
      setText(next)
      requestAnimationFrame(resize)
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void submit()
  }

  return (
    <div className="px-4 pb-4">
      <form
        onSubmit={onSubmit}
        className="mx-auto flex w-full max-w-3xl flex-col gap-2 rounded-2xl border bg-background p-2 shadow-sm focus-within:ring-2 focus-within:ring-ring/40"
      >
        <Textarea
          ref={ref}
          rows={1}
          value={text}
          placeholder="Ask about a filing — e.g. how did AWS margin trend from 2021 to 2025?"
          className="max-h-[200px] min-h-9 resize-none border-0 bg-transparent px-2 py-1.5 shadow-none focus-visible:ring-0 dark:bg-transparent"
          onChange={(event) => {
            setText(event.target.value)
            resize()
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault()
              void submit()
            }
          }}
        />
        <div className="flex items-center justify-between px-1">
          <span className="text-xs text-muted-foreground">
            Enter to send, Shift+Enter for a new line
          </span>
          {busy ? (
            <Button
              type="button"
              size="icon"
              variant="secondary"
              aria-label="Stop generating"
              onClick={onStop}
            >
              <Square className="size-3.5 fill-current" />
            </Button>
          ) : (
            <Button
              type="submit"
              size="icon"
              aria-label="Send message"
              disabled={text.trim().length === 0}
            >
              <ArrowUp />
            </Button>
          )}
        </div>
      </form>
    </div>
  )
}
