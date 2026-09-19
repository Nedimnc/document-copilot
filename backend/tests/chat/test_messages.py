from app.chat.messages import UIMessageIn, extract_text, last_user_text, ui_payload


def test_extract_text_joins_text_parts():
    message = UIMessageIn(
        id="1",
        role="user",
        parts=[
            {"type": "text", "text": "Hello "},
            {"type": "step-start"},
            {"type": "text", "text": "world"},
        ],
    )

    assert extract_text(message) == "Hello world"


def test_last_user_text_uses_latest_user_message():
    messages = [
        UIMessageIn(role="user", parts=[{"type": "text", "text": "first"}]),
        UIMessageIn(role="assistant", parts=[{"type": "text", "text": "ok"}]),
        UIMessageIn(role="user", parts=[{"type": "text", "text": " second "}]),
    ]

    assert last_user_text(messages) == "second"


def test_last_user_text_requires_user_text():
    try:
        last_user_text(
            [UIMessageIn(role="assistant", parts=[{"type": "text", "text": "only"}])]
        )
    except ValueError as exc:
        assert "user message" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_ui_payload_wraps_text():
    assert ui_payload("hi") == {"parts": [{"type": "text", "text": "hi"}]}
