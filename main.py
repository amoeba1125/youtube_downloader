import os
import json
from pathlib import Path
import time
import yt_dlp
import urllib.request
import socket
import subprocess

BASE_DIR = Path(__file__).parent        # main.py 所在資料夾

with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

def resolve_path(template, **kwargs):
    p = Path(template.format(**kwargs))
    if p.is_absolute():
        return p
    return (BASE_DIR / p).resolve()

IF_BGUTIL = False                       # 是否已啟用bgutil
CHANNELS_FILE = config["channels_text"] # 下載的頻道列表
MAX_ENTRIES = config["max_entries"]     # 每種類型抓最新幾支
SLEEP_SECONDS = config["sleep_seconds"] # 檢查間隔時間
DOWNLOAD = config.get("download", {})

def is_bgutil_running() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:4416", timeout=1) as resp:
            return resp.status == 200
    except Exception:
        return False

def is_video_downloaded(video_id, folder):
    """檢查影片是否已下載"""
    return any(video_id in f for f in os.listdir(folder))

def download_video(video_url, folder):
    """下載影片到指定資料夾"""
    ydl_opts = {
        'outtmpl': os.path.join(folder, '%(title)s [%(id)s].%(ext)s'),
        'format': 'bestvideo+bestaudio/best',
        'quiet': False,
        'live_from_start': True  # 確保抓完整直播
    }
    if is_bgutil_running():
        ydl_opts['extractor_args'] = {
            'youtubepot-bgutilhttp': [
                'base_url=http://127.0.0.1:4416'
            ]
        }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

def fetch_and_download(url, folder, filter_func):
    """抓取影片列表，依 filter_func 過濾後下載"""
    ydl_opts = {'quiet': True, 'extract_flat': True}  # extract_flat=True 先抓列表
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            entries = info.get('entries', [info])  # 影片列表或單支影片

            count = 0
            for entry in entries:
                if count >= MAX_ENTRIES and MAX_ENTRIES >= 0:
                    break
                if entry is None:
                    continue

                video_id = entry.get('id')
                video_url = entry.get('url') or entry.get('webpage_url')
                if not video_id or not video_url:
                    continue
                if filter_func(entry):
                    if is_video_downloaded(video_id, folder):
                        print(f"已存在: {video_id} -> {folder}")
                    else:
                        print(f"下載影片: {video_id} -> {folder}")
                        download_video(video_url, folder)
                    count += 1

        except Exception as e:
            print(f"抓取 {url} 失敗: {e}")

def main_loop():
    while True:
        if not os.path.exists(CHANNELS_FILE):
            print(f"{CHANNELS_FILE} 不存在")
            time.sleep(SLEEP_SECONDS)
            continue

        with open(CHANNELS_FILE, 'r', encoding='utf-8') as f:
            channels = []
            for line in f:
                stripped = line.strip()
                if stripped:
                    channels.append('/'.join(stripped.split('/')[:4]))

        for channel in channels:
            ydl_opts = {'quiet': True, 'extract_flat': True}  # extract_flat=True 先抓列表
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(channel, download=False)
                    print(info.get('channel'))

                    channel_name = info.get('channel')
                    # 根目錄資料夾
                    raw_paths = config["paths"]
                    paths = {
                        name: resolve_path(template, channel_name=channel_name)
                        for name, template in raw_paths.items()
                    }

                    VIDEOS_DIR = paths["videos"]    # 影片存放路徑
                    SHORTS_DIR = paths["shorts"]    # 短影片存放路徑
                    LIVE_DIR = paths["live"]        # 直播存放路徑
                    POSTS_DIR = paths["posts"]      # 貼文存放路徑(未實作)

                    for folder in [VIDEOS_DIR, SHORTS_DIR, LIVE_DIR, POSTS_DIR]:
                        os.makedirs(folder, exist_ok=True)
                    PAGES = {
                        "videos": (
                            f"{channel}/videos",
                            VIDEOS_DIR,
                            lambda e: not e.get("is_live") and not e.get("was_live") and e.get('live_status') != 'is_upcoming'
                        ),
                        "shorts": (
                            f"{channel}/shorts",
                            SHORTS_DIR,
                            lambda e: True
                        ),
                        "live": (
                            f"{channel}/streams",
                            LIVE_DIR,
                            lambda e: e.get("is_live") or e.get("was_live") or e.get("live_status") == "was_live"
                        )
                    }
                    pages = [
                        page
                        for key, page in PAGES.items()
                        if DOWNLOAD.get(key, False)
                    ]

                    print("[debug] pages:", pages)

                    for url, folder, filter_func in pages:
                        fetch_and_download(url, folder, filter_func)

                except Exception as e:
                    print(f"處理 {channel} 時發生錯誤: {e}")

        time.sleep(SLEEP_SECONDS)

if __name__ == "__main__":
    main_loop()
