# ChatAGH API

**Description:**
The ChatAGH API provides an intelligent conversational interface for answering questions related to **AGH University**.
It processes a list of chat messages (representing the conversation history) and returns a generated response based on the current query and context.

---

## **Endpoint**

`POST /api/chat`

---

## **Request Body**

```json
{
  "messages": [
    { "role": "user", "content": "Kiedy zaczyna się rekrutacja na AGH?" }
  ]
}
```

**Parameters:**
- **messages** *(list)* — The full chat history.
  Each message must include:
  - **role** — `"user"` or `"assistant"`
  - **content** — The text of the message.

---

## **Response**

```json
{
  "response": "Rekrutacja na studia w AGH zwykle rozpoczyna się w czerwcu. Dokładne terminy można znaleźć na stronie rekrutacja.agh.edu.pl."
}
```

**Fields:**
- **response** *(string)* — The model’s generated answer to the most recent user message.


---

## **Notes**
- The API supports **multi-turn conversations** — include previous exchanges in the `messages` list for contextual answers.
- Responses are generated using the internal **ChatGraph** orchestration system, which integrates retrieval, reasoning, and generation components.
- Default execution mode can be customized through the `config` parameter.
