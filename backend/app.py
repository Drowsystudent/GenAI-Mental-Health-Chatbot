# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS

from llm import generate_reply

app = Flask(__name__)
CORS(app)

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Missing 'message'"}), 400

    reply, safety_level = generate_reply(user_message)
    return jsonify({"reply": reply, "safety_level": safety_level}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
