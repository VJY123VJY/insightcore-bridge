from flask import Flask, request, jsonify

app = Flask(__name__)

# In mock_insightflow_receiver.py, after app = Flask(__name__)

@app.route('/', methods=['GET'])
def status_check():
    """Simple status check for the root path."""
    return "InsightFlow Mock Receiver is online. Use POST on /receive_telemetry.", 200

# The rest of the file remains the same.

@app.route('/receive_telemetry', methods=['GET', 'POST'])
def receive_telemetry():
    """Simulates the InsightFlow server endpoint.

    - POST: accepts JSON telemetry and returns 200 on success.
    - GET: returns a short help/health JSON so a browser or probe doesn't trigger 405.
    """
    if request.method == 'GET':
        return jsonify({
            "status": "ok",
            "message": "InsightFlow endpoint. POST JSON telemetry to this URL.",
            "allowed_methods": ["POST"]
        }), 200

    # POST handling
    data = request.get_json(silent=True)
    if data:
        print(f"--- RECEIVED EVENT (Source: {data.get('source', 'N/A')}) ---")
        print(f"Event Type: {data.get('event_type')}, State: {data.get('state')}, Reward: {data.get('reward')}")
        print("---------------------------------------------------------")
        return jsonify({"status": "received", "timestamp": data.get("timestamp")}), 200
    return jsonify({"status": "error", "message": "No data received"}), 400

if __name__ == '__main__':
    print("InsightFlow Mock Receiver listening on http://127.0.0.1:8000/receive_telemetry")
    print("Run 'python insights_generator.py' in a separate terminal to send events.")
    app.run(port=8000, debug=False)