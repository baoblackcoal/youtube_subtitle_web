// YouTube Subtitle Downloader Main Script
document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const videoUrlInput = document.getElementById('videoUrl');
  const getSubtitlesBtn = document.getElementById('getSubtitles');
  const pasteAndGetBtn = document.getElementById('pasteAndGet');
  const statusElement = document.getElementById('status');
  const subtitleTypeRadios = document.querySelectorAll('input[name="subtitleType"]');
  const formatRadios = document.querySelectorAll('input[name="format"]');

  // Add focus class to input group when focused
  videoUrlInput.addEventListener('focus', () => {
    document.querySelector('.input-group').classList.add('focused');
  });

  videoUrlInput.addEventListener('blur', () => {
    document.querySelector('.input-group').classList.remove('focused');
  });

  // Handle paste and download
  pasteAndGetBtn.addEventListener('click', async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        videoUrlInput.value = text;
        getSubtitles();
      }
    } catch (error) {
      showStatus('error', '无法访问剪贴板：' + error.message);
    }
  });

  // Handle get subtitles button
  getSubtitlesBtn.addEventListener('click', getSubtitles);

  async function getSubtitles() {
    const videoUrl = videoUrlInput.value.trim();
    
    if (!videoUrl) {
      showStatus('error', '请输入有效的YouTube视频链接');
      return;
    }

    if (!isValidYouTubeUrl(videoUrl)) {
      showStatus('error', '请输入有效的YouTube视频链接');
      return;
    }

    // Get selected options
    const subtitleType = getSelectedRadioValue(subtitleTypeRadios);
    const format = getSelectedRadioValue(formatRadios);

    showStatus('loading', '正在下载字幕，请稍候...');

    try {
      // Make request to API
      const response = await fetch('/api/download-subtitle', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          videoUrl,
          subtitleType,
          format
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || '下载字幕时出错');
      }

      // Get filename from the Content-Disposition header if available
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'subtitle.' + format;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1];
        }
      }

      // Handle the response - either text or blob depending on format
      if (format === 'txt') {
        const subtitleText = await response.text();
        downloadTextFile(subtitleText, filename);
      } else {
        const blob = await response.blob();
        downloadBlobFile(blob, filename);
      }

      showStatus('success', '字幕下载成功！');
    } catch (error) {
      showStatus('error', '下载字幕失败：' + error.message);
      console.error('Error downloading subtitles:', error);
    }
  }

  // Helper functions
  function getSelectedRadioValue(radios) {
    for (const radio of radios) {
      if (radio.checked) {
        return radio.value;
      }
    }
    return null;
  }

  function isValidYouTubeUrl(url) {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
    return youtubeRegex.test(url);
  }

  function showStatus(type, message) {
    statusElement.className = 'status ' + type;
    statusElement.textContent = message;
    statusElement.style.display = 'block';
  }

  function downloadTextFile(text, filename) {
    const blob = new Blob([text], { type: 'text/plain' });
    downloadBlobFile(blob, filename);
  }

  function downloadBlobFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 100);
  }
}); 