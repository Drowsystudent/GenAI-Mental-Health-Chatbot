import os
import boto3
import logging
from datetime import datetime
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

# Set up CloudWatch logging
cloudwatch = boto3.client('logs', region_name='us-east-2')

def log_to_cloudwatch(log_group, message, level='INFO'):
    """Send log to CloudWatch"""
    try:
        log_stream = datetime.now().strftime('%Y-%m-%d')

        # Create log stream if it doesn't exist
        try:
            cloudwatch.create_log_stream(
                logGroupName=log_group,
                logStreamName=log_stream
            )
        except cloudwatch.exceptions.ResourceAlreadyExistsException:
            pass

        # Put log event
        cloudwatch.put_log_events(
            logGroupName=log_group,
            logStreamName=log_stream,
            logEvents=[{
                'timestamp': int(datetime.now().timestamp() * 1000),
                'message': f"[{level}] {message}"
            }]
        )
    except Exception as e:
        print(f"CloudWatch logging failed: {e}")

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

    # Log API call to CloudWatch
    log_to_cloudwatch(
            '/mental-health-chatbot/api-calls',
            f"User message received: {user_message[:50]}..."
    )

    reply, safety_level = generate_reply(user_message, history)

    # Log crisis detection if needed
    if safety_level == 'imminent':
        log_to_cloudwatch(
            '/mental-health-chatbot/crisis-detection',
            f"Crisis detected! Message: {user_message}",
            level='ALERT'
        )

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
