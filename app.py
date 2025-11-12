from typing import Any

from flask import Flask, request, jsonify
from werkzeug.exceptions import BadRequest
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv

from chat_agh.graph import ChatGraph
from chat_agh.utils.chat_history import ChatHistory

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


def extract_text(result : str | dict | None) -> str:
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
    try:
        payload = request.get_json(force=True, silent=False)
        messages = parse_messages(payload)

        chat_history = ChatHistory(messages=messages)
        result = chat_graph.invoke(chat_history)

        text = extract_text(result).strip()
        if not text:
            text = "Przepraszam, podczas generowania odpowiedzi wystąpił błąd. Spróbuj ponownie."
        return jsonify({"response": text})

    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {e}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)
