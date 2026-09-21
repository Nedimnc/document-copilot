from pydantic_ai.messages import ModelRequest, ModelResponse

from app.chat.messages import (
    UIMessageIn,
    extract_text,
    last_user_text,
    ui_messages_to_model_history,
    ui_payload,
)


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


def test_ui_messages_to_model_history_excludes_latest_user_turn():
    messages = [
        UIMessageIn(role="user", parts=[{"type": "text", "text": "first"}]),
        UIMessageIn(role="assistant", parts=[{"type": "text", "text": "answer one"}]),
        UIMessageIn(role="user", parts=[{"type": "text", "text": "second question"}]),
    ]
    history = ui_messages_to_model_history(messages, max_turns=6)
    assert len(history) == 2
    assert isinstance(history[0], ModelRequest)
    assert isinstance(history[1], ModelResponse)


def test_ui_messages_to_model_history_caps_turns():
    messages: list[UIMessageIn] = []
    for index in range(4):
        messages.append(
            UIMessageIn(role="user", parts=[{"type": "text", "text": f"q{index}"}])
        )
        messages.append(
            UIMessageIn(
                role="assistant", parts=[{"type": "text", "text": f"a{index}"}]
            )
        )
    messages.append(
        UIMessageIn(role="user", parts=[{"type": "text", "text": "latest"}])
    )
    history = ui_messages_to_model_history(messages, max_turns=2)
    assert len(history) == 4
