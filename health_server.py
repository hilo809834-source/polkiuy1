from flask import Flask, jsonify
import os

app = Flask(__name__)

# Health status - can be toggled for testing
HEALTHY = True

@app.route('/health')
def health():
    global HEALTHY
    if HEALTHY:
        return jsonify({"status": "healthy"}), 200
    else:
        return jsonify({"status": "unhealthy", "error": "service degraded"}), 503

@app.route('/')
def index():
    return "Staging Server v1.0.0 - AI Dev Studio"

@app.route('/toggle-health')
def toggle_health():
    global HEALTHY
    HEALTHY = not HEALTHY
    status = "healthy" if HEALTHY else "unhealthy"
    return jsonify({"status": status, "http_code": 200 if HEALTHY else 503})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 9000))
    app.run(host='0.0.0.0', port=port, threaded=True)
