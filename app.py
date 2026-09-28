import os
import time
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    session_id = data.get("sessionId")
    message_id = data.get("messageId")
    uuid_info = data.get("uuid")
    message_name = data.get("messageName")
    payload = data.get("payload", {})

    if message_name == "RUN_APP":
        answer_text = "Привет! Я твой личный ассистент. Спрашивай что угодно."
    else:
        user_text = payload.get("message", {}).get("original_text", "")
        answer_text = ask_gemini(user_text) if user_text else "Извини, я не расслышал вопрос."

    response = {
        "sessionId": session_id,
        "messageId": message_id,
        "uuid": uuid_info,
        "messageName": "ANSWER_TO_USER",
        "payload": {
            "pronounceText": answer_text,
            "pronounceTextType": "application/text",
            "items": [{"bubble": {"text": answer_text}}],
            "finished": False
        }
    }
    return jsonify(response)


MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.1-flash-lite"]


def ask_gemini(user_text):
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }
    start = time.time()
    for model in MODELS:
        left = 5.5 - (time.time() - start)
        if left < 1:
            break
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Ты голосовой ассистент. Отвечай по-русски, очень кратко: одним-двумя предложениями, без markdown и списков."},
                {"role": "user", "content": user_text}
            ],
            "max_tokens": 200
        }
        r = None
        try:
            r = requests.post(GEMINI_URL, headers=headers, json=body, timeout=min(left, 3.5))
            r.raise_for_status()
            print("GEMINI OK", model, round(time.time() - start, 2), "s")
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print("GEMINI ERROR", model, round(time.time() - start, 2), "s:", repr(e))
            if r is not None:
                print("GEMINI RESPONSE:", r.text[:300])
    return "Извини, сейчас нейросеть перегружена. Повтори вопрос чуть позже."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
