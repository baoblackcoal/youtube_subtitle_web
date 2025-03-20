from http.server import BaseHTTPRequestHandler
import yt_dlp
import os
import tempfile
import re
import json
import urllib.parse
import platform
import base64

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
        try:
            # 使用增强的选项配置yt-dlp
            # 这些设置有助于避免YouTube的机器人检测
            options = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': subtitle_type == 'auto',
                'subtitleslangs': ['en'],
                'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'ignoreerrors': True,
                'nocheckcertificate': True,
                'geo_bypass': True,
                'extractor_retries': 3,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
                'referer': 'https://www.youtube.com/',
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer': 'https://www.youtube.com/',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'same-origin',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                },
                'cookies': 'NID=522=aSTI7tSivz2pnnxYHQjeySiJ2o_Z1k_3w990X98xxkggTJpbMCYlYwvIu2mQb8qDEhMTwmg-3pApPWMx50VRYC_5xI9hzTozIWebkWt6cU4Rk1eyUjb1C6n9T7dLWE29p5ERFQ5jM0i6bJTbdFT3UNcEKWnc1Xmyt52SCDIAEMIem2D4fw0x__qf6deMmiU3kFsXHhuX_gzfyOPaQIFkm0ZIu1mAVL-t; OTZ=7976947_24_24__24_; PREF=f4=4000000&tz=Asia.Shanghai&f7=100&f5=20000&f6=400; VISITOR_INFO1_LIVE=AMOZMRTemKo; VISITOR_PRIVACY_METADATA=CgJKUBIEGgAgSw%3D%3D; LOGIN_INFO=AFmmF2swRAIgMDsVZ2yLUvJsME0XIKWrkOV8rWNgcf2GQ5UiOmmUwjsCIBkSIW19aoMtpGxUA-RH5FH0JcKgdSE_jGAWMDeBnTMx:QUQ3MjNmek9rTEIwUGEwMzhPMmNuNVZaTWNpTGhCNDFkNzBwVnNWVk9VblhvQUM1bmhTbEt2Uk5HdmdfSWhObktrTDRERV9OVENhWUcxNjF6dVhRZm9IMjQwNkRJa1JSaktmLUhpMkZJZ0xkVUx6UHNTR3Z6NlhndGZEUUlxSFNpS3pWN3F2UkxnRGRJSlFyVG9HcWhjUHFORUZMdkVHYTB5NmFwS0lFS0h2U2xCZnZNR09MTV9Id3hMY1RrS00ydUp0aDE5X1E5Rnp2dEdHcDYtTm5RNVF0c1Y1NnJyTlJVUQ==; YSC=9cMLw3QcyTw; __Secure-ROLLOUT_TOKEN=CMvA-OLJ4Jj90AEQoNnfyqaEjAMYm520nciVjAM%3D; SIDCC=AKEyXzU1oNXTw0Y9pHfG31rK9lxDEyG77iLAfAXGLTVe5R8lIJhsJoT3sNve52EVJN6YBnAkazU; __Secure-1PSIDCC=AKEyXzUnTD5VVmq6aXBHp8JzAErQ2z5Hl6zneUErvhX6FeQo-1zDg_ZWFkIWSWo1lD6twUxpJw; __Secure-1PSIDTS=sidts-CjIB7pHptX3NhgznzOyzUK0LPOTb-4XpNXPGstz_GVZd1zr-EF_MEyC-NLaghs_re_8xKhAA; __Secure-3PSIDTS=sidts-CjIB7pHptX3NhgznzOyzUK0LPOTb-4XpNXPGstz_GVZd1zr-EF_MEyC-NLaghs_re_8xKhAA; HSID=ASeGW39drSFkBEm6n; SSID=AfWU4v6SKKi8fJOPB; APISID=Ja0LblLwNjiu-Vle/AITI1RS-2e9lAQmJB; SAPISID=fIXz0o7pCQhgaqNc/AM1issXQYONkB-ZYB; __Secure-1PAPISID=fIXz0o7pCQhgaqNc/AM1issXQYONkB-ZYB; __Secure-3PAPISID=fIXz0o7pCQhgaqNc/AM1issXQYONkB-ZYB; SID=g.a000uwiV5RVeyYXCZTglHOOTBodRktt-tEJu917uYhmj4E0Jm4AuQzBcq5yLhbvqawZ0wehGHQACgYKASgSARQSFQHGX2MigxBjhgFS0st7bSmWbTaxWxoVAUF8yKoYAt4R4Ai9OEplfSH2Noyk0076; __Secure-1PSID=g.a000uwiV5RVeyYXCZTglHOOTBodRktt-tEJu917uYhmj4E0Jm4AuC1T2JLfLrdKhXA_E3B_iIgACgYKAU4SARQSFQHGX2Micm-HaVJ5vZpW6FNT96X_JxoVAUF8yKpGipXzZxP2xWlr1D-lmz7G0076; __Secure-3PSID=g.a000uwiV5RVeyYXCZTglHOOTBodRktt-tEJu917uYhmj4E0Jm4AuMrFKoNLmeN9zPcipNxAycgACgYKAYkSARQSFQHGX2MissJZVEohcG7Gxnl9aunrxRoVAUF8yKrgNVvabUx_gDQLZmeDd-hF0076; __Secure-3PSIDCC=AKEyXzUajbZu3FdjJyO8cDxK0s6DVlL4h8ZEwy55fngqj-p9wUniWYKWojxjXJkwJA-f1QN6_Aw'
            }
            
            # 尝试添加更多认证选项
            # 这些选项适用于Python API
            auth_headers = {
                'Origin': 'https://www.youtube.com',
                'X-YouTube-Client-Name': '1',
                'X-YouTube-Client-Version': '2.20210721.00.00'
            }
            options['http_headers'].update(auth_headers)
            
            # Extract video information using yt-dlp
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(video_url, download=True)
                
                if not info:
                    # 如果提取失败，尝试只获取基本信息
                    simple_options = dict(options)
                    simple_options.update({
                        'skip_download': True,
                        'writesubtitles': False,
                        'writeautomaticsub': False,
                        'extract_flat': True,
                        'dumpjson': True,
                        'quiet': True,
                        'cookiesfrombrowser': 'chrome'
                    })
                    with yt_dlp.YoutubeDL(simple_options) as simple_ydl:
                        info = simple_ydl.extract_info(video_url, download=False)
                
                # 检查是否成功获取信息
                if not info:
                    return None, None, "无法获取视频信息"
                
                video_id = info.get('id', extract_video_id(video_url))
                title = info.get('title', "YouTube Video")
                
                # 寻找下载的字幕文件
                subtitle_file = None
                subtitle_pattern = '*.en.*vtt' if subtitle_type == 'auto' else '*.en.vtt'
                
                # 检查临时目录中所有的文件
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if file.endswith(".en.vtt"):
                            # 确认是正确的自动生成或手动字幕
                            if subtitle_type == 'auto' and 'auto' in file:
                                subtitle_file = file_path
                                break
                            elif subtitle_type != 'auto' and 'auto' not in file:
                                subtitle_file = file_path
                                break
                
                if not subtitle_file and subtitle_type == 'auto':
                    # 对于自动字幕，尝试使用最常见的命名模式
                    possible_file = os.path.join(temp_dir, f"{video_id}.en.vtt")
                    if os.path.exists(possible_file):
                        subtitle_file = possible_file
                
                # 如果找不到字幕文件，尝试使用YouTube API直接获取字幕
                if not subtitle_file or not os.path.exists(subtitle_file):
                    return None, None, f"未找到字幕文件，请确认视频{video_id}有英文字幕"
                
                # 读取VTT文件内容
                with open(subtitle_file, 'r', encoding='utf-8') as f:
                    vtt_content = f.read()
                
                # 转换为请求的格式
                if format == 'vtt':
                    return vtt_content, f"{title}.vtt", "application/vtt"
                elif format == 'srt':
                    srt_content = convert_vtt_to_srt(vtt_content)
                    return srt_content, f"{title}.srt", "application/srt"
                else:  # txt
                    txt_content = convert_vtt_to_txt(vtt_content)
                    return txt_content, f"{title}.txt", "text/plain"
        
        except Exception as e:
            # 记录异常信息
            error_message = f"字幕下载失败: {str(e)}"
            print(f"Error: {error_message}")
            return None, None, error_message

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
            
            # 验证URL
            if not video_url or 'youtube.com' not in video_url and 'youtu.be' not in video_url:
                # 发送错误响应
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': '请输入有效的YouTube视频URL'}).encode('utf-8'))
                return
            
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
                self.wfile.write(json.dumps({'error': '下载字幕失败：' + str(mime_type)}).encode('utf-8'))
        
        except Exception as e:
            # 处理异常
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_msg = str(e)
            print(f"Server error: {error_msg}")
            self.wfile.write(json.dumps({'error': error_msg}).encode('utf-8'))
    
    def do_GET(self):
        """处理GET请求（健康检查）"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            'status': 'ok',
            'message': 'YouTube字幕下载API服务正常'
        }).encode('utf-8')) 