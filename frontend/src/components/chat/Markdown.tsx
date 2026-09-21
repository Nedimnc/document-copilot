import { cloneElement, isValidElement, type ReactElement, type ReactNode } from "react"
import ReactMarkdown, { type Components } from "react-markdown"
import remarkGfm from "remark-gfm"

import { cn } from "@/lib/utils"

const CITATION = /(\[\d+\])/g

type CitationClick = (index: number) => void

// Turn "[3]" markers in the model's text into buttons that open the citation in
// the side panel. Recurses through inline elements (bold, italic, links) so a
// marker inside emphasis still becomes interactive.
function linkifyCitations(
  children: ReactNode,
  onCitationClick: CitationClick | undefined,
  maxIndex: number,
): ReactNode {
  if (typeof children === "string") {
    const parts = children.split(CITATION)
    if (parts.length === 1) {
      return children
    }
    return parts.map((part, i) => {
      const match = /^\[(\d+)\]$/.exec(part)
      if (!match) {
        return part
      }
      const n = Number(match[1])
      // Only linkify markers we actually have a source for; leave stray ones as text.
      if (!onCitationClick || n < 1 || n > maxIndex) {
        return part
      }
      return (
        <button
          key={i}
          type="button"
          onClick={() => onCitationClick(n)}
          className="mx-0.5 cursor-pointer align-super text-[0.7em] font-medium text-link hover:underline"
          aria-label={`Open source ${n}`}
        >
          [{n}]
        </button>
      )
    })
  }

  if (Array.isArray(children)) {
    return children.map((child, i) => (
      <span key={i} className="contents">
        {linkifyCitations(child, onCitationClick, maxIndex)}
      </span>
    ))
  }

  if (isValidElement(children)) {
    const el = children as ReactElement<{ children?: ReactNode }>
    return cloneElement(
      el,
      undefined,
      linkifyCitations(el.props.children, onCitationClick, maxIndex),
    )
  }

  return children
}

function makeComponents(
  onCitationClick: CitationClick | undefined,
  citationCount: number,
): Components {
  const link = (nodes: ReactNode) =>
    linkifyCitations(nodes, onCitationClick, citationCount)

  return {
    p: ({ children }) => <p className="my-2 first:mt-0 last:mb-0">{link(children)}</p>,
    ul: ({ children }) => (
      <ul className="my-2 ml-5 list-disc space-y-1 marker:text-muted-foreground">
        {children}
      </ul>
    ),
    ol: ({ children }) => (
      <ol className="my-2 ml-5 list-decimal space-y-1 marker:text-muted-foreground">
        {children}
      </ol>
    ),
    li: ({ children }) => <li className="pl-1">{link(children)}</li>,
    h1: ({ children }) => (
      <h1 className="mt-4 mb-2 text-lg font-semibold first:mt-0">{link(children)}</h1>
    ),
    h2: ({ children }) => (
      <h2 className="mt-4 mb-2 text-base font-semibold first:mt-0">{link(children)}</h2>
    ),
    h3: ({ children }) => (
      <h3 className="mt-3 mb-1 text-sm font-semibold first:mt-0">{link(children)}</h3>
    ),
    strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
    em: ({ children }) => <em className="italic">{children}</em>,
    a: ({ children, href }) => (
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="font-medium text-link underline underline-offset-2"
      >
        {children}
      </a>
    ),
    blockquote: ({ children }) => (
      <blockquote className="my-2 border-l-2 border-border pl-3 text-muted-foreground">
        {children}
      </blockquote>
    ),
    code: ({ className, children }) => {
      const isBlock = /language-/.test(className ?? "")
      if (isBlock) {
        return <code className="font-mono text-[0.85em]">{children}</code>
      }
      return (
        <code className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]">
          {children}
        </code>
      )
    },
    pre: ({ children }) => (
      <pre className="my-2 overflow-x-auto rounded-md bg-muted p-3 text-[0.85em]">
        {children}
      </pre>
    ),
    hr: () => <hr className="my-4 border-border" />,
    table: ({ children }) => (
      <div className="my-3 overflow-x-auto">
        <table className="w-full border-collapse text-sm tabular-nums">{children}</table>
      </div>
    ),
    thead: ({ children }) => <thead className="border-b border-border">{children}</thead>,
    tr: ({ children }) => <tr className="border-b border-border last:border-0">{children}</tr>,
    th: ({ children }) => (
      <th className="px-3 py-1.5 text-left font-semibold">{link(children)}</th>
    ),
    td: ({ children }) => <td className="px-3 py-1.5 align-top">{link(children)}</td>,
  }
}

export function Markdown({
  content,
  citationCount = 0,
  onCitationClick,
  className,
}: {
  content: string
  citationCount?: number
  onCitationClick?: CitationClick
  className?: string
}) {
  return (
    <div className={cn("text-sm leading-relaxed break-words", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={makeComponents(onCitationClick, citationCount)}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
