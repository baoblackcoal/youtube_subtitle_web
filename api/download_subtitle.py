from http.server import BaseHTTPRequestHandler
import yt_dlp
import os
import tempfile
import re
import json
import urllib.parse

# Function to extract video ID from URL
def extract_video_id(url):
    if 'youtu.be' in url:
        # Short URL format
        video_id = url.split('/')[-1].split('?')[0]
    else:
        # Regular youtube.com URL
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        video_id = query_params.get('v', [''])[0]
    
    return video_id

# Function to convert WebVTT to SRT format
def convert_vtt_to_srt(vtt_content):
    # Remove WebVTT header
    content = re.sub(r'^WEBVTT\s*\n', '', vtt_content)
    
    # Replace WebVTT timestamps with SRT timestamps
    # WebVTT: 00:00:00.000 --> 00:00:05.000
    # SRT: 00:00:00,000 --> 00:00:05,000
    content = re.sub(r'(\d{2}:\d{2}:\d{2})\.(\d{3})', r'\1,\2', content)
    
    # Add sequence numbers
    lines = content.split('\n\n')
    srt_lines = []
    
    for i, line in enumerate(lines, 1):
        if line.strip():
            srt_lines.append(f"{i}\n{line}")
    
    return '\n\n'.join(srt_lines)

# Function to convert WebVTT to plain text
def convert_vtt_to_txt(vtt_content):
    # Remove WebVTT header
    content = re.sub(r'^WEBVTT\s*\n', '', vtt_content)
    
    # Remove timestamps and line numbers
    content = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', '', content)
    content = re.sub(r'^\d+$', '', content, flags=re.MULTILINE)
    
    # Clean up extraneous whitespace and newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = re.sub(r'^\s+', '', content, flags=re.MULTILINE)
    
    return content.strip()

def download_subtitle(video_url, subtitle_type='auto', format='txt'):
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set options for yt-dlp
        options = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': subtitle_type == 'auto',
            'subtitleslangs': ['en'],
            'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
            'quiet': True,
        }
        
        try:
            # Extract video information using yt-dlp
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(video_url, download=True)
                video_id = info.get('id')
                title = info.get('title', 'Unknown')
                
                # Determine the downloaded subtitle file
                subtitle_file = None
                if subtitle_type == 'auto':
                    subtitle_file = os.path.join(temp_dir, f"{video_id}.en.vtt")
                else:
                    # Look for manually added subtitle files
                    for file in os.listdir(temp_dir):
                        if file.endswith(".en.vtt") and not file.endswith(".auto.en.vtt"):
                            subtitle_file = os.path.join(temp_dir, file)
                            break
                
                if not subtitle_file or not os.path.exists(subtitle_file):
                    return None, None, "未找到字幕文件"
                
                # Read the VTT file content
                with open(subtitle_file, 'r', encoding='utf-8') as f:
                    vtt_content = f.read()
                
                # Convert to requested format
                if format == 'vtt':
                    return vtt_content, f"{title}.vtt", "application/vtt"
                elif format == 'srt':
                    srt_content = convert_vtt_to_srt(vtt_content)
                    return srt_content, f"{title}.srt", "application/srt"
                else:  # txt
                    txt_content = convert_vtt_to_txt(vtt_content)
                    return txt_content, f"{title}.txt", "text/plain"
        
        except Exception as e:
            return None, None, str(e)

# 确保handler类名是小写的，并且继承自BaseHTTPRequestHandler
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """处理POST请求下载字幕"""
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
            
            # 提取参数
            video_url = data.get('videoUrl', '')
            subtitle_type = data.get('subtitleType', 'auto')
            format_type = data.get('format', 'txt')
            
            # 下载字幕
            content, filename, mime_type = download_subtitle(video_url, subtitle_type, format_type)
            
            if content:
                # 发送成功响应
                self.send_response(200)
                self.send_header('Content-Type', mime_type)
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.end_headers()
                
                # 发送字幕内容
                if isinstance(content, str):
                    self.wfile.write(content.encode('utf-8'))
                else:
                    self.wfile.write(content)
            else:
                # 发送错误响应
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': '下载字幕失败'}).encode('utf-8'))
        
        except Exception as e:
            # 处理异常
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
    
    def do_GET(self):
        """处理GET请求（健康检查）"""
        self.send_response(405)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'error': '只接受POST请求'}).encode('utf-8')) 