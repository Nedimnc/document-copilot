INSUFFICIENT_EVIDENCE_INSTRUCTION = (
    "The corpus does not contain enough evidence to answer this question."
)

INSUFFICIENT_EVIDENCE_USER_MESSAGE = (
    "I don't have enough evidence in the SEC filing corpus to answer that. "
    "Try rephrasing or asking about a company or topic covered by the loaded filings."
)

GROUNDING_VALIDATION_FAILURE_MESSAGE = (
    "I couldn't verify that answer against the retrieved filing passages. "
    "Please rephrase your question or ask for a narrower fact from the corpus."
)

LLM_UNAVAILABLE_MESSAGE = (
    "The assistant is temporarily unavailable. Please try again in a moment."
)
