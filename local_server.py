from flask import Flask, request, send_from_directory, Response, jsonify
import os
import datetime
import json
import io
import sys
from urllib.parse import parse_qs

# 导入我们的字幕下载模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api.download_subtitle import download_subtitle

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
    """本地Flask实现的字幕下载API"""
    try:
        # 获取请求JSON数据
        data = request.get_json()
        
        # 提取参数
        video_url = data.get('videoUrl', '')
        subtitle_type = data.get('subtitleType', 'auto')
        format_type = data.get('format', 'txt')
        
        # 下载字幕
        content, filename, mime_type = download_subtitle(video_url, subtitle_type, format_type)
        
        if content:
            # 创建带有字幕内容的响应
            response = Response(content, mimetype=mime_type)
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        else:
            return jsonify({'error': f'下载字幕失败'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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