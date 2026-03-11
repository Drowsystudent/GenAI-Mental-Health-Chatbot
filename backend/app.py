import os
print("RUNNING FROM:", os.getcwd())
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge

from llm import generate_reply

app = Flask(__name__)

# Limit request size to 32 KB
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024


@app.errorhandler(RequestEntityTooLarge)
def length_error(e):
    return jsonify({
        "error": "Exceeded maximum message length.",
        "max_bytes": app.config["MAX_CONTENT_LENGTH"]
    }), 413


CORS(app, resources={
    r"/chat": {
        "origins": [
            "http://localhost:3000",
        ]
    }
})


@app.get("/health")
def health():
    return jsonify({"ok": True})


@app.post("/chat")
def chat():
    if request.content_type != "application/json":
        return jsonify({"error": "Content-Type must be application/json."}), 415

    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Missing 'message'"}), 400

    reply, safety_level = generate_reply(user_message)

    return jsonify({
        "reply": reply,
        "safety_level": safety_level
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
