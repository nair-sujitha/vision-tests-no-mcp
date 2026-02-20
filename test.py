import requests
import os
import asyncio

api_key = "your api key"

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

headers = {
    "x-goog-api-key": api_key,
    "Content-Type": "application/json"
}

data = {
    "contents": [
        {
            "parts": [
                {"text": "Say hello"}
            ]
        }
    ]
}

async def main():
    response = requests.post(url, headers=headers, json=data)
    print(response.status_code)
    print(response.text)


if __name__ == "__main__":
    asyncio.run(main())