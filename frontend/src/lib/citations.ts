export type MessageCitation = {
  id: string
  chunk_id: string
  document_id: string
  sort_order: number
  excerpt: string
  page: number | null
  ticker: string
  company_name: string
  filing_type: string
  fiscal_year: number
  filing_date: string
  source_url: string
  section: string | null
}
