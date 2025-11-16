import logging
import time
from typing import Any

from flask import Flask, request, jsonify, Response, stream_with_context
from werkzeug.exceptions import BadRequest
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv

from chat_agh.graph import ChatGraph
from chat_agh.utils.chat_history import ChatHistory

logger = logging.getLogger("chat_agh_api")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

load_dotenv(".env")

app = Flask(__name__)
chat_graph = ChatGraph()

ROLE_MAP = {
    "user": HumanMessage,
    "assistant": AIMessage,
    "system": SystemMessage,
}


def parse_messages(payload: dict) -> list:
    if not isinstance(payload, dict):
        raise BadRequest("Request body must be a JSON object.")

    msgs = payload.get("messages")
    if not isinstance(msgs, list) or len(msgs) == 0:
        raise BadRequest("Field 'messages' must be a non-empty list.")

    converted = []
    for i, m in enumerate(msgs):
        if not isinstance(m, dict):
            raise BadRequest(f"Message at index {i} must be an object.")
        role = m.get("role")
        content = m.get("content")
        if role not in ROLE_MAP:
            raise BadRequest(
                f"Invalid role at index {i}: {role!r}. Use 'user' or 'assistant'."
            )
        if not isinstance(content, str) or not content.strip():
            raise BadRequest(
                f"Message 'content' at index {i} must be a non-empty string."
            )
        converted.append(ROLE_MAP[role](content))
    return converted


def extract_text(result: str | dict | None) -> str:
    """
    Be resilient to various return shapes:
    - {'response': '...'}
    - AIMessage(content='...')
    - plain string
    - {'content': '...'}
    """
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        if "response" in result and isinstance(result["response"], str):
            return result["response"]
        if "content" in result and isinstance(result["content"], str):
            return result["content"]

    content = getattr(result, "content", None)
    if isinstance(content, str):
        return content

    return str(result)


@app.post("/api/chat")
def chat() -> Any:
    start_time = time.time()
    try:
        payload = request.get_json(force=True, silent=False)
        logger.info(
            "POST /api/chat from %s, raw payload size=%s bytes",
            request.remote_addr,
            len(request.data) if request.data is not None else 0,
        )
        logger.debug("Payload: %s", payload)

        messages = parse_messages(payload)
        logger.info("Parsed %d messages", len(messages))

        try:
            first_user_msg = next(
                (m.content for m in messages if isinstance(m, HumanMessage)), None
            )
            if first_user_msg:
                logger.info("First user message: %s", first_user_msg[:200])
        except Exception:
            logger.debug("Failed to extract first user message", exc_info=True)

        chat_history = ChatHistory(messages=messages)
        logger.info("Invoking ChatGraph...")
        result = chat_graph.invoke(chat_history)
        logger.info("ChatGraph.invoke finished")

        text = extract_text(result).strip()
        if not text:
            logger.warning("Empty response from ChatGraph, returning fallback message")
            text = "Przepraszam, podczas generowania odpowiedzi wystąpił błąd. Spróbuj ponownie."

        duration = time.time() - start_time
        logger.info("Request handled in %.3f s", duration)

        return jsonify({"response": text})

    except BadRequest as e:
        logger.warning("BadRequest in /api/chat: %s", e)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("Unhandled exception in /api/chat: %s", e)
        return jsonify({"error": f"Internal server error: {e}"}), 500


@app.post("/api/chat_stream")
def chat_stream() -> Any:
    """
    Streaming endpoint using chat_graph.stream(chat_history).

    Returns newline-delimited chunks (plain text) as they are produced.
    """
    try:
        payload = request.get_json(force=True, silent=False)
        logger.info(
            "POST /api/chat_stream from %s, raw payload size=%s bytes",
            request.remote_addr,
            len(request.data) if request.data is not None else 0,
        )
        logger.debug("Payload: %s", payload)

        messages = parse_messages(payload)
        logger.info("Parsed %d messages for streaming", len(messages))

        chat_history = ChatHistory(messages=messages)

        def generate():
            logger.info("Starting streaming response")
            try:
                for chunk in chat_graph.stream(chat_history):
                    text = extract_text(chunk)
                    if not text:
                        continue
                    logger.debug("Stream chunk: %s", text[:200])
                    yield text + "\n"
                logger.info("Streaming finished normally")
            except Exception as e:
                logger.exception("Error during streaming: %s", e)
                yield f"[STREAM_ERROR] {e}\n"

        return Response(
            stream_with_context(generate()),
            mimetype="text/plain",
        )

    except BadRequest as e:
        logger.warning("BadRequest in /api/chat_stream: %s", e)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("Unhandled exception in /api/chat_stream: %s", e)
        return jsonify({"error": f"Internal server error: {e}"}), 500


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Starting Flask app on 0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000, debug=True)