import os
print("RUNNING FROM:", os.getcwd())
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge

from llm import generate_reply

app = Flask(__name__)

# Check if build folder exists (production) or not (local dev)
build_folder = os.path.join(os.path.dirname(__file__), '../frontend/build')
if os.path.exists(build_folder):
    app = Flask(__name__, static_folder=build_folder, static_url_path='')
else:
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
            "http://100.53.127.71",
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
    history = data.get("history") or []

    if not user_message:
        return jsonify({"error": "Missing 'message'"}), 400

    reply, safety_level = generate_reply(user_message, history)

    return jsonify({
        "reply": reply,
        "safety_level": safety_level
    }), 200


# Serve React app in production (only if build folder exists)
if os.path.exists(build_folder):
    @app.route('/')
    def serve():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>')
    def serve_static(path):
        if os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
