# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge

from llm import generate_reply

app = Flask(__name__)

#limit request size against potential attackers dropping large payloads. Currently set at 32kb
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024

#error handling if message exceeds MAX_CONTENT_LENGTH
@app.errorhandler(RequestEntityTooLarge)
def length_error(e):   
    return jsonify({
        "error" : "Exceeded maximum message length.",
        "max_bytes" : app.config["MAX_CONTENT_LENGTH"]
    }), 413


CORS(app, resources={r"/chat": 
                        {"origins=": [
                            "http://localhost:3000",
                            #we can add more alias urls later
                            ]
                        }
})

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.post("/chat")
def chat():
    if request.content_type != "application/json":
        return jsonify({"error: Content type must be application/json."}), 415

    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Missing 'message'"}), 400

    #TODO: we should probably rate limit generate_reply so an attacker cant rapidly consume tokens 
    reply, safety_level = generate_reply(user_message)      
    return jsonify({"reply": reply, "safety_level": safety_level}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True) #we will need to update later. debug=true and host=0.0.0.0 are bad vunerabilties
