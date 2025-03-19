from flask import Flask, request, send_from_directory, Response, jsonify
import os
import datetime
import sys

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/date')
def date_api():
    # Simplified implementation of the date API
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return Response(current_time, mimetype='text/plain')

@app.route('/api/ip/<path:path>')
def ip_query(path):
    # Simplified implementation of the IP API
    return jsonify({
        "query": path,
        "ip": request.remote_addr,
        "path": request.path
    })

@app.route('/api/download-subtitle', methods=['POST'])
def download_subtitle_api():
    # Import the flask_handler function from download_subtitle.py
    from api.download_subtitle import flask_handler
    return flask_handler()

@app.route('/api/<path:path>')
def api_catch_all(path):
    # Simplified implementation of the web API
    key = request.args.get('key')
    return Response(f"<h1>Flask</h1><p>You visited: /{path}</p><p>key={key}</p>", mimetype="text/html")

@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    else:
        return send_from_directory('.', '404.html'), 404

if __name__ == '__main__':
    print("Server running at http://localhost:3000")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True, port=3000, host='0.0.0.0') 