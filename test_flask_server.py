import requests

API_URL = "http://localhost:8000/api/chat"

if __name__ == "__main__":
    payload = {
        "messages": [
            {"role": "user", "content": "Kiedy zaczyna się rekrutacja na AGH?"}
        ]
    }

    response = requests.post(API_URL, json=payload)

    if response.status_code == 200:
        data = response.json()
        print("✅ Response:", data["response"])
    else:
        print("❌ Error:", response.status_code, response.text)
