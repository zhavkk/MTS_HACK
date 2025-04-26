#!/usr/bin/env python3
import requests
import json

def main():
    session_id = input("Enter SESSION_ID: ").strip()
    if not session_id:
        print("SESSION_ID cannot be empty")
        return

    url = f"http://localhost:8000/sessions/{session_id}/messages"
    headers = {"Content-Type": "application/json"}

    print(f"Ready to send messages to session {session_id}.")
    print("Type your message and press Enter. Ctrl+C to exit.")

    try:
        while True:
            content = input("> ").strip()
            if not content:
                continue

            payload = {
                "role": "user",
                "content": content
            }

            try:
                resp = requests.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                # Выводим ответ сервера (если есть)
                try:
                    data = resp.json()
                    print("Server response:", json.dumps(data, ensure_ascii=False))
                except ValueError:
                    print("Message sent successfully.")
            except requests.HTTPError as http_err:
                print(f"HTTP error: {http_err} — {resp.text}")
            except requests.RequestException as err:
                print(f"Request error: {err}")

    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()