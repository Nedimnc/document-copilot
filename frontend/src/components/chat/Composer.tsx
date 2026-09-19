import { useState, type FormEvent } from "react"

export function Composer({
  disabled,
  onSend,
}: {
  disabled: boolean
  onSend: (text: string) => Promise<void>
}) {
  const [text, setText] = useState("")

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const next = text.trim()
    if (!next || disabled) {
      return
    }
    setText("")
    try {
      await onSend(next)
    } catch {
      setText(next)
    }
  }

  return (
    <form
      className="border-t border-zinc-200 bg-white px-4 py-3"
      onSubmit={onSubmit}
    >
      <div className="mx-auto flex max-w-2xl gap-2">
        <textarea
          className="min-h-11 flex-1 resize-none rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900"
          name="message"
          rows={1}
          placeholder="Ask about a filing…"
          value={text}
          disabled={disabled}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault()
              event.currentTarget.form?.requestSubmit()
            }
          }}
        />
        <button
          className="rounded-md bg-zinc-900 px-3 py-2 text-sm text-white disabled:opacity-60"
          type="submit"
          disabled={disabled || text.trim().length === 0}
        >
          Send
        </button>
      </div>
    </form>
  )
}
