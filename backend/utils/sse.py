"""
Shared Server-Sent Events (SSE) formatting utilities.

Provides a consistent event format for all generation endpoints,
eliminating duplication across route handlers.
"""

import json
from typing import Any


def format_sse_event(event: Any) -> str:
    """
    Format a generation event into an SSE-compatible string.

    Handles all standard event types produced by generation workflows:
    thread_id, progress, complete, and error.

    Args:
        event: A dict with a "type" key, or any other value.

    Returns:
        Formatted SSE string ready to be yielded in a StreamingResponse.
    """
    if not isinstance(event, dict):
        return f"data: {json.dumps({'content': str(event)})}\n\n"

    event_type = event.get("type", "data")

    if event_type == "thread_id":
        return f"event: thread_id\ndata: {json.dumps({'thread_id': event['thread_id']})}\n\n"

    if event_type == "progress":
        progress_data = {
            "message_key": event.get("message_key", event.get("message", "")),
        }
        if "params" in event:
            progress_data["params"] = event["params"]
        return f"event: progress\ndata: {json.dumps(progress_data)}\n\n"

    if event_type == "complete":
        return f"event: complete\ndata: {json.dumps(event['data'])}\n\n"

    if event_type == "error":
        error_data = {}
        if "message_key" in event:
            error_data["message_key"] = event["message_key"]
        else:
            # Fallback: use a generic key — never forward raw messages
            error_data["message_key"] = "errors.generationFailed"
        return f"event: error\ndata: {json.dumps(error_data)}\n\n"

    # Fallback for unknown event types
    return f"data: {json.dumps(event)}\n\n"


def format_sse_error(error_payload: dict) -> str:
    """
    Format an error payload into an SSE error event.

    Args:
        error_payload: Dict with error details (typically from classify_error).

    Returns:
        Formatted SSE error string.
    """
    return f"event: error\ndata: {json.dumps(error_payload)}\n\n"
