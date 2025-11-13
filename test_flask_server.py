import requests

HOST = "http://localhost:8000/api/chat"

if __name__ == "__main__":
    payload = {
        "messages": [
            {"role": "user", "content": "Jak zostać studentem AGH?"}
        ]
    }

    response = requests.post(HOST, json=payload)

    if response.status_code == 200:
        print("Response:", response.json())
    else:
        print("Error:", response.status_code, response.text)
