/** Matches Docling triplet table serialization (row, col = value). */
const TRIPLET_ARTIFACT_RE =
  /(?:^|[.\s])([^,\n]{1,80},\s*[^=\n]{1,80}\s*=\s*[^.\n]{0,40})/g

/** Chunk fragments often use "16 = 383,285. Total net sales" instead of "Total net sales, 16 = …". */
const ALT_TRIPLET_RE = /(\d+)\s*=\s*([^.\n]+?)\.\s*([^,\n]+?)(?=,\s*\d+\s*=|$)/g

export type FormattedCitationExcerpt =
  | { kind: "prose"; text: string }
  | { kind: "markdown"; text: string }
  // Readable narrative recovered after removing shredded table fragments. `raw`
  // keeps the original text so the reader can still inspect what was dropped.
  | { kind: "partial"; text: string; raw: string }
  // Nothing readable survives — the excerpt is only orphaned table fragments.
  | { kind: "garbledTable"; raw: string }

// Removes "Label, 27 = 13." style fragments. The value class is number/symbol only,
// so it stops at the first real word — that's what lets prose after the table survive.
const TRIPLET_LABEL_STRIP_RE =
  /[A-Za-z][A-Za-z0-9 ()%$/-]*?,\s*\d+\s*=\s*[\d.,%$()-]*\s*/g
// Second pass for label-less "27 = 13" leftovers.
const TRIPLET_ORPHAN_STRIP_RE = /,?\s*\b\d+\s*=\s*[\d.,%$()-]*\s*/g

function countTripletSignals(text: string): number {
  const standard = text.match(TRIPLET_ARTIFACT_RE)?.length ?? 0
  const alt = text.match(ALT_TRIPLET_RE)?.length ?? 0
  return standard + alt
}

export function looksLikeTripletTableSerialization(text: string): boolean {
  return countTripletSignals(text) >= 3
}

function normalizeWhitespace(text: string): string {
  return text.replace(/\s+/g, " ").trim()
}

function looksLikeMarkdownTable(text: string): boolean {
  return /^\s*\|.+\|\s*$/m.test(text)
}

/** Strip shredded table fragments, leaving whatever real prose was stored alongside them. */
function stripTripletArtifacts(text: string): string {
  return text
    .replace(TRIPLET_LABEL_STRIP_RE, " ")
    .replace(TRIPLET_ORPHAN_STRIP_RE, " ")
    .replace(/\s*\|\s*/g, " ") // page-footer pipes: "Apple Inc. | 2024 Form 10-K | 24"
    .replace(/\s+([.,;%])/g, "$1")
    .replace(/(?:^|\s)[.,;:%]+(?=\s|$)/g, " ") // orphaned punctuation tokens
    .replace(/^[\s.,;:%|-]+/, "")
    .replace(/\s{2,}/g, " ")
    .trim()
}

/** Cheap "is there a real sentence left" check after we strip the table junk. */
function looksLikeProse(text: string): boolean {
  const words = text.match(/[A-Za-z]{2,}/g) ?? []
  return text.length >= 40 && words.length >= 8
}

/** Turn raw chunk excerpts into a display shape the citation panel can render cleanly. */
export function formatCitationExcerpt(raw: string): FormattedCitationExcerpt {
  const text = raw.trim()
  if (!text) {
    return { kind: "prose", text: "" }
  }

  if (looksLikeMarkdownTable(text)) {
    return { kind: "markdown", text }
  }

  if (looksLikeTripletTableSerialization(text)) {
    // The excerpt often starts with a shredded table and *ends* with real prose.
    // Recover the prose if there's enough of it; otherwise admit it's unreadable.
    const cleaned = stripTripletArtifacts(text)
    if (looksLikeProse(cleaned) && !looksLikeTripletTableSerialization(cleaned)) {
      return { kind: "partial", text: cleaned, raw: normalizeWhitespace(text) }
    }
    return { kind: "garbledTable", raw: normalizeWhitespace(text) }
  }

  return { kind: "prose", text: normalizeWhitespace(text) }
}
