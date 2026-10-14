from __future__ import annotations

import json
import time
from typing import Any, Iterable, Iterator
from uuid import uuid4


CHAT_COMPLETION_PARAMS = {
    "frequency_penalty",
    "logit_bias",
    "n",
    "presence_penalty",
    "seed",
    "stop",
    "stream",
    "temperature",
    "top_p",
    "user",
}


def responses_request_to_chat_completions(payload: dict[str, Any]) -> dict[str, Any]:
    chat_payload: dict[str, Any] = {}

    if "model" in payload:
        chat_payload["model"] = payload["model"]

    messages: list[dict[str, Any]] = []
    instructions = payload.get("instructions")
    if instructions:
        messages.extend(_instructions_to_messages(instructions))

    input_value = payload.get("input")
    if input_value is not None:
        messages.extend(_input_to_messages(input_value))

    if messages:
        chat_payload["messages"] = messages

    for key in CHAT_COMPLETION_PARAMS:
        if key in payload:
            chat_payload[key] = payload[key]

    max_tokens = payload.get("max_output_tokens", payload.get("max_completion_tokens"))
    if max_tokens is not None:
        chat_payload["max_tokens"] = max_tokens

    reasoning = payload.get("reasoning")
    if isinstance(reasoning, dict) and reasoning.get("effort") is not None:
        chat_payload["reasoning_effort"] = reasoning["effort"]

    tools = _responses_tools_to_chat_tools(payload.get("tools"))
    if tools:
        chat_payload["tools"] = tools

    tool_choice = payload.get("tool_choice")
    if tool_choice is not None:
        chat_payload["tool_choice"] = _responses_tool_choice_to_chat_tool_choice(tool_choice)

    return chat_payload


def chat_completion_to_response(chat_completion: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    response_id = _response_id(chat_completion.get("id"))
    created_at = int(chat_completion.get("created") or time.time())
    model = chat_completion.get("model") or request.get("model")
    output: list[dict[str, Any]] = []
    output_text_parts: list[str] = []
    reasoning_text_parts: list[str] = []

    for choice in chat_completion.get("choices", []):
        if not isinstance(choice, dict):
            continue
        message = choice.get("message")
        if not isinstance(message, dict):
            continue

        content = message.get("content")
        if content:
            text = _content_to_text(content)
            if text:
                output_text_parts.append(text)
                output.append(
                    {
                        "id": f"msg_{uuid4().hex}",
                        "type": "message",
                        "status": "completed",
                        "role": "assistant",
                        "content": [
                            {
                                "type": "output_text",
                                "text": text,
                                "annotations": [],
                            }
                        ],
                    }
                )

        reasoning_content = message.get("reasoning_content")
        if reasoning_content:
            reasoning_text = _content_to_text(reasoning_content)
            if reasoning_text:
                reasoning_text_parts.append(reasoning_text)

        for tool_call in message.get("tool_calls") or []:
            if not isinstance(tool_call, dict):
                continue
            function = tool_call.get("function") if isinstance(tool_call.get("function"), dict) else {}
            call_id = tool_call.get("id") or f"call_{uuid4().hex}"
            output.append(
                {
                    "id": call_id,
                    "type": "function_call",
                    "status": "completed",
                    "call_id": call_id,
                    "name": function.get("name", ""),
                    "arguments": function.get("arguments", ""),
                }
            )

    if not output_text_parts and reasoning_text_parts:
        text = "".join(reasoning_text_parts)
        output_text_parts.append(text)
        output.append(
            {
                "id": f"msg_{uuid4().hex}",
                "type": "message",
                "status": "completed",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": text,
                        "annotations": [],
                    }
                ],
            }
        )

    usage = _responses_usage(chat_completion.get("usage"))
    return {
        "id": response_id,
        "object": "response",
        "created_at": created_at,
        "status": "completed",
        "error": None,
        "incomplete_details": None,
        "instructions": request.get("instructions"),
        "max_output_tokens": request.get("max_output_tokens"),
        "model": model,
        "output": output,
        "output_text": "".join(output_text_parts),
        "parallel_tool_calls": bool(request.get("parallel_tool_calls", False)),
        "previous_response_id": request.get("previous_response_id"),
        "reasoning": request.get("reasoning"),
        "store": bool(request.get("store", False)),
        "temperature": request.get("temperature"),
        "text": request.get("text", {"format": {"type": "text"}}),
        "tool_choice": request.get("tool_choice", "auto"),
        "tools": request.get("tools", []),
        "top_p": request.get("top_p"),
        "truncation": request.get("truncation", "disabled"),
        "usage": usage,
    }


def chat_stream_to_response_stream(
    chunks: Iterable[bytes],
    request: dict[str, Any],
) -> Iterator[bytes]:
    response_id = f"resp_{uuid4().hex}"
    message_id = f"msg_{uuid4().hex}"
    created_at = int(time.time())
    model = request.get("model")
    sequence = 1
    started = False
    text_parts: list[str] = []
    reasoning_parts: list[str] = []
    buffer = ""

    response_shell = {
        "id": response_id,
        "object": "response",
        "created_at": created_at,
        "status": "in_progress",
        "error": None,
        "incomplete_details": None,
        "instructions": request.get("instructions"),
        "model": model,
        "output": [],
        "parallel_tool_calls": bool(request.get("parallel_tool_calls", False)),
        "previous_response_id": request.get("previous_response_id"),
        "reasoning": request.get("reasoning"),
        "store": bool(request.get("store", False)),
        "temperature": request.get("temperature"),
        "text": request.get("text", {"format": {"type": "text"}}),
        "tool_choice": request.get("tool_choice", "auto"),
        "tools": request.get("tools", []),
        "top_p": request.get("top_p"),
        "truncation": request.get("truncation", "disabled"),
        "usage": None,
    }

    yield _sse("response.created", {"type": "response.created", "response": response_shell}, sequence)

    for raw_chunk in chunks:
        buffer += raw_chunk.decode("utf-8", errors="replace")
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            event = _parse_chat_sse_line(line.strip())
            if event is None:
                continue
            if event == "[DONE]":
                yield from _finish_response_stream(
                    response_shell,
                    response_id,
                    message_id,
                    text_parts,
                    reasoning_parts,
                    sequence + 1,
                    started,
                )
                return
            if not isinstance(event, dict):
                continue
            if event.get("model"):
                model = event["model"]
                response_shell["model"] = model
            delta = _first_choice_delta(event)
            if not delta:
                continue
            text_delta = _content_to_text(delta.get("content"))
            reasoning_delta = _content_to_text(delta.get("reasoning_content"))
            if reasoning_delta:
                reasoning_parts.append(reasoning_delta)
            if not text_delta:
                continue
            if not started:
                sequence += 1
                yield _sse(
                    "response.output_item.added",
                    {
                        "type": "response.output_item.added",
                        "output_index": 0,
                        "item": {
                            "id": message_id,
                            "type": "message",
                            "status": "in_progress",
                            "role": "assistant",
                            "content": [],
                        },
                    },
                    sequence,
                )
                sequence += 1
                yield _sse(
                    "response.content_part.added",
                    {
                        "type": "response.content_part.added",
                        "item_id": message_id,
                        "output_index": 0,
                        "content_index": 0,
                        "part": {"type": "output_text", "text": "", "annotations": []},
                    },
                    sequence,
                )
                started = True
            text_parts.append(text_delta)
            sequence += 1
            yield _sse(
                "response.output_text.delta",
                {
                    "type": "response.output_text.delta",
                    "item_id": message_id,
                    "output_index": 0,
                    "content_index": 0,
                    "delta": text_delta,
                },
                sequence,
            )

    yield from _finish_response_stream(
        response_shell,
        response_id,
        message_id,
        text_parts,
        reasoning_parts,
        sequence + 1,
        started,
    )


def _instructions_to_messages(instructions: Any) -> list[dict[str, Any]]:
    if isinstance(instructions, str):
        return [{"role": "developer", "content": instructions}]
    return _input_to_messages(instructions)


def _input_to_messages(input_value: Any) -> list[dict[str, Any]]:
    if isinstance(input_value, str):
        return [{"role": "user", "content": input_value}]
    if isinstance(input_value, dict):
        message = _response_item_to_chat_message(input_value)
        return [message] if message else []
    if isinstance(input_value, list):
        messages = []
        for item in input_value:
            message = _response_item_to_chat_message(item)
            if message:
                messages.append(message)
        return messages
    return []


def _response_item_to_chat_message(item: Any) -> dict[str, Any] | None:
    if isinstance(item, str):
        return {"role": "user", "content": item}
    if not isinstance(item, dict):
        return None

    item_type = item.get("type")
    if item_type == "function_call_output":
        return {
            "role": "tool",
            "tool_call_id": item.get("call_id"),
            "content": _content_to_text(item.get("output")),
        }

    if item_type == "function_call":
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": item.get("call_id") or item.get("id"),
                    "type": "function",
                    "function": {
                        "name": item.get("name", ""),
                        "arguments": item.get("arguments", ""),
                    },
                }
            ],
        }

    role = item.get("role", "user")
    if role not in {"system", "developer", "user", "assistant", "tool"}:
        role = "user"

    message: dict[str, Any] = {
        "role": role,
        "content": _content_to_text(item.get("content", item.get("text", ""))),
    }
    if role == "tool" and item.get("tool_call_id"):
        message["tool_call_id"] = item["tool_call_id"]
    return message


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, (int, float, bool)):
        return str(content)
    if isinstance(content, list):
        parts = [_content_to_text(part) for part in content]
        return "\n".join(part for part in parts if part)
    if isinstance(content, dict):
        if "text" in content:
            return _content_to_text(content["text"])
        if "output" in content:
            return _content_to_text(content["output"])
        if "input_text" in content:
            return _content_to_text(content["input_text"])
        return ""
    return ""


def _responses_tools_to_chat_tools(tools: Any) -> list[dict[str, Any]]:
    if not isinstance(tools, list):
        return []
    chat_tools = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        if tool.get("type") != "function":
            continue
        if isinstance(tool.get("function"), dict):
            chat_tools.append(tool)
            continue
        chat_tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {}),
                },
            }
        )
    return chat_tools


def _responses_tool_choice_to_chat_tool_choice(tool_choice: Any) -> Any:
    if not isinstance(tool_choice, dict):
        return tool_choice
    if tool_choice.get("type") == "function" and "name" in tool_choice:
        return {
            "type": "function",
            "function": {"name": tool_choice["name"]},
        }
    return tool_choice


def _responses_usage(usage: Any) -> dict[str, Any] | None:
    if not isinstance(usage, dict):
        return None
    return {
        "input_tokens": usage.get("prompt_tokens", usage.get("input_tokens", 0)),
        "output_tokens": usage.get("completion_tokens", usage.get("output_tokens", 0)),
        "total_tokens": usage.get("total_tokens", 0),
    }


def _response_id(upstream_id: Any) -> str:
    if isinstance(upstream_id, str) and upstream_id.startswith("resp_"):
        return upstream_id
    if isinstance(upstream_id, str) and upstream_id:
        return f"resp_{upstream_id}"
    return f"resp_{uuid4().hex}"


def _parse_chat_sse_line(line: str) -> Any:
    if not line.startswith("data:"):
        return None
    data = line[5:].strip()
    if not data:
        return None
    if data == "[DONE]":
        return data
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None


def _first_choice_delta(event: dict[str, Any]) -> dict[str, Any] | None:
    choices = event.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    choice = choices[0]
    if not isinstance(choice, dict):
        return None
    delta = choice.get("delta")
    return delta if isinstance(delta, dict) else None


def _finish_response_stream(
    response_shell: dict[str, Any],
    response_id: str,
    message_id: str,
    text_parts: list[str],
    reasoning_parts: list[str],
    sequence: int,
    started: bool,
) -> Iterator[bytes]:
    text = "".join(text_parts)
    if not text and reasoning_parts:
        text = "".join(reasoning_parts)
        started = True
        yield _sse(
            "response.output_item.added",
            {
                "type": "response.output_item.added",
                "output_index": 0,
                "item": {
                    "id": message_id,
                    "type": "message",
                    "status": "in_progress",
                    "role": "assistant",
                    "content": [],
                },
            },
            sequence,
        )
        sequence += 1
        yield _sse(
            "response.content_part.added",
            {
                "type": "response.content_part.added",
                "item_id": message_id,
                "output_index": 0,
                "content_index": 0,
                "part": {"type": "output_text", "text": "", "annotations": []},
            },
            sequence,
        )
        sequence += 1
        yield _sse(
            "response.output_text.delta",
            {
                "type": "response.output_text.delta",
                "item_id": message_id,
                "output_index": 0,
                "content_index": 0,
                "delta": text,
            },
            sequence,
        )
        sequence += 1
    if started:
        yield _sse(
            "response.output_text.done",
            {
                "type": "response.output_text.done",
                "item_id": message_id,
                "output_index": 0,
                "content_index": 0,
                "text": text,
                "logprobs": [],
            },
            sequence,
        )
        sequence += 1
        yield _sse(
            "response.content_part.done",
            {
                "type": "response.content_part.done",
                "item_id": message_id,
                "output_index": 0,
                "content_index": 0,
                "part": {"type": "output_text", "text": text, "annotations": []},
            },
            sequence,
        )
        sequence += 1
        yield _sse(
            "response.output_item.done",
            {
                "type": "response.output_item.done",
                "output_index": 0,
                "item": {
                    "id": message_id,
                    "type": "message",
                    "status": "completed",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": text, "annotations": []}],
                },
            },
            sequence,
        )
        response_shell["output"] = [
            {
                "id": message_id,
                "type": "message",
                "status": "completed",
                "role": "assistant",
                "content": [{"type": "output_text", "text": text, "annotations": []}],
            }
        ]

    response_shell.update(
        {
            "id": response_id,
            "status": "completed",
            "output_text": text,
        }
    )
    sequence += 1
    yield _sse("response.completed", {"type": "response.completed", "response": response_shell}, sequence)
    yield b"data: [DONE]\n\n"


def _sse(event: str, data: dict[str, Any], sequence: int) -> bytes:
    payload = dict(data)
    payload.setdefault("type", event)
    payload.setdefault("sequence_number", sequence)
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n".encode("utf-8")
