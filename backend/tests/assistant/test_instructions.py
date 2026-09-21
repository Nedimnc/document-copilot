from app.assistant.instructions import (
    BASE_SYSTEM_INSTRUCTIONS,
    full_system_instructions,
)


def test_base_instructions_include_trust_rules():
    text = BASE_SYSTEM_INSTRUCTIONS.lower()
    assert "cite" in text
    assert "investment advice" in text
    assert "retrieved passages" in text


def test_full_system_instructions_appends_grounding():
    combined = full_system_instructions(grounding_addendum="Passage [1] foo")
    assert "Passage [1] foo" in combined
    assert "Document Copilot" in combined
