import requests

HOST = "http://localhost:8000/api/chat_stream"

if __name__ == "__main__":
    payload = {
        "messages": [
            {"role": "user", "content": "Jak zostać studentem AGH?"}
        ]
    }

    response = requests.post(HOST, json=payload, stream=True)

    if response.status_code == 200:
        print("Streaming response:")
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            print("Chunk:", line)
    else:
        print("Error:", response.status_code, response.text)