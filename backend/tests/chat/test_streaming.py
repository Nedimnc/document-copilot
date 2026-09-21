from app.chat.streaming import chunk_text, format_sse, iter_text_part_events


def test_format_sse_encodes_json_and_done():
    assert format_sse({"type": "start"}) == b'data: {"type":"start"}\n\n'
    assert format_sse("[DONE]") == b"data: [DONE]\n\n"


def test_iter_text_part_events_follows_ui_message_protocol():
    events = list(
        iter_text_part_events(message_id="msg-1", text="Hello there", text_id="txt")
    )

    assert events[0] == {"type": "start", "messageId": "msg-1"}
    assert events[1] == {"type": "start-step"}
    assert events[2] == {"type": "text-start", "id": "txt"}
    assert events[-3] == {"type": "text-end", "id": "txt"}
    assert events[-2] == {"type": "finish-step"}
    assert events[-1] == {"type": "finish"}
    assert "".join(
        event["delta"] for event in events if event["type"] == "text-delta"
    ) == "Hello there"


def test_chunk_text_splits_evenly():
    assert chunk_text("abcdefgh", size=3) == ["abc", "def", "gh"]
