import os
import json
import time
import threading
from datetime import datetime
from googleapiclient.discovery import build
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO

# ======== CONFIGURATION ========
API_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
CHANNEL_ID = 'UCoxFxZirbfLvy9tres71eSA'
DATA_LOG_FILE = 'stream_analysis_log.json'

CHAT_COLLECTION_DURATION_SEC = 30
BOT_ESTIMATION_INTERVAL_SEC = 60

LURKER_ADJUSTMENT_FACTOR = 0.25
MIN_CHAT_VIEWER_RATIO_FOR_PRIMARY_ESTIMATION = 0.02
SUSPICIOUSLY_HIGH_MESSAGE_COUNT_PER_USER = 10

# ======== YouTube API Setup ========
youtube = build('youtube', 'v3', developerKey=API_KEY)

# ======== Bot Phrase Heuristics ========
bot_like_phrases = [
    "as an ai language model", "i am an ai", "according to my training",
    "i don't have personal opinions", "i cannot perform that action",
    "here is a summary", "i am not capable of", "my training data suggests",
    "based on your input", "as a machine", "i do not experience emotions",
    "i'm a bot", "i am here to assist", "in conclusion", "let me clarify",
    "i cannot browse the internet", "i apologize for the confusion",
    "thank you for your question"
]

# ======== Core Functions ========
def get_live_stream_id(channel_id):
    res = youtube.search().list(
        part='id',
        channelId=channel_id,
        eventType='live',
        type='video',
        maxResults=1
    ).execute()

    items = res.get('items', [])
    return items[0]['id']['videoId'] if items else None

def get_channel_info(channel_id):
    res = youtube.channels().list(
        part='snippet',
        id=channel_id
    ).execute()
    items = res.get('items', [])
    if not items:
        return None, None
    snippet = items[0]['snippet']
    return snippet.get('title'), snippet.get('thumbnails', {}).get('default', {}).get('url')

def get_stream_stats(video_id):
    res = youtube.videos().list(
        part='liveStreamingDetails,statistics',
        id=video_id
    ).execute()

    items = res.get('items', [])
    if not items:
        return None

    details = items[0].get('liveStreamingDetails', {})
    return {
        'concurrentViewers': int(details.get('concurrentViewers', 0)),
        'activeChatId': details.get('activeLiveChatId')
    }

def get_chat_analysis(chat_id, duration_sec):
    unique_authors = {}
    total_messages = 0
    end_time = time.time() + duration_sec
    next_page_token = None

    while time.time() < end_time:
        res = youtube.liveChatMessages().list(
            liveChatId=chat_id,
            part='snippet,authorDetails',
            pageToken=next_page_token,
            maxResults=200
        ).execute()

        for item in res.get('items', []):
            total_messages += 1
            author_id = item['authorDetails']['channelId']
            message = item['snippet'].get('displayMessage', '').lower()
            is_bot_phrase = any(phrase in message for phrase in bot_like_phrases)

            if author_id not in unique_authors:
                unique_authors[author_id] = {
                    'displayName': item['authorDetails']['displayName'],
                    'messageCount': 1,
                    'isModerator': item['authorDetails']['isChatModerator'],
                    'isOwner': item['authorDetails']['isChatOwner'],
                    'botPhraseHits': 1 if is_bot_phrase else 0,
                    'messages': [message]
                }
            else:
                user = unique_authors[author_id]
                user['messageCount'] += 1
                if is_bot_phrase:
                    user['botPhraseHits'] += 1
                user['messages'].append(message)

        next_page_token = res.get('nextPageToken')
        wait_time = res.get('pollingIntervalMillis', 2000) / 1000
        time.sleep(wait_time)

    suspicious = 0
    ai_like_bots = 0
    for user in unique_authors.values():
        unique_msgs = len(set(user['messages']))
        msg_similarity = unique_msgs / len(user['messages']) if user['messages'] else 1
        spammer = user['messageCount'] > SUSPICIOUSLY_HIGH_MESSAGE_COUNT_PER_USER and not (user['isModerator'] or user['isOwner'])
        likely_ai = (
            user['botPhraseHits'] > 0 or
            msg_similarity < 0.5 or
            (user['messageCount'] > 5 and all(len(m) > 15 and m.endswith('.') for m in user['messages']))
        )

        if spammer:
            suspicious += 1
        if likely_ai and not user['isModerator'] and not user['isOwner']:
            ai_like_bots += 1

    return {
        'uniqueChatterCount': len(unique_authors),
        'totalMessagesCollected': total_messages,
        'averageMessagesPerChatter': total_messages / len(unique_authors) if unique_authors else 0,
        'potentiallySuspiciousChatters': suspicious,
        'detectedAiLikeBots': ai_like_bots
    }

def estimate_viewers(concurrent_viewers, chat_analysis):
    adj_unique = max(0, chat_analysis['uniqueChatterCount'] - chat_analysis['potentiallySuspiciousChatters'])
    raw_ratio = chat_analysis['uniqueChatterCount'] / concurrent_viewers if concurrent_viewers else 0
    adj_ratio = adj_unique / concurrent_viewers if concurrent_viewers else 0

    if adj_unique == 0:
        estimated_real = 0
    elif adj_ratio >= MIN_CHAT_VIEWER_RATIO_FOR_PRIMARY_ESTIMATION:
        estimated_real = round(adj_unique / LURKER_ADJUSTMENT_FACTOR)
    else:
        estimated_real = round(concurrent_viewers * adj_ratio)

    estimated_real = min(max(adj_unique, estimated_real), concurrent_viewers)
    estimated_bots = concurrent_viewers - estimated_real

    return {
        'estimatedRealViewers': estimated_real,
        'estimatedBotViewers': estimated_bots,
        'rawChatToViewerRatio': raw_ratio,
        'adjustedChatToViewerRatio': adj_ratio
    }

def log_to_file(entry):
    if os.path.exists(DATA_LOG_FILE):
        with open(DATA_LOG_FILE, 'r') as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
            except:
                data = []
    else:
        data = []

    data.append(entry)
    with open(DATA_LOG_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ======== GUI Setup ========
class BotDetectorGUI:
    def __init__(self, root):
        self.root = root
        root.title("YouTube Live Bot Detector")
        root.geometry("350x600")
        root.resizable(False, False)

        # Variables
        self.status = tk.StringVar()
        self.viewer_count = tk.StringVar()
        self.real_count = tk.StringVar()
        self.bot_count = tk.StringVar()
        self.ai_bot_count = tk.StringVar()
        self.channel_name_var = tk.StringVar()
        self.channel_id_var = tk.StringVar()

        # Container frame for centering
        self.container = ttk.Frame(root)
        self.container.pack(expand=True, fill=tk.BOTH)

        # Load and display IBB Image
        try:
            ibb_url = "https://i.ibb.co/3Yd91xMq/e08c1b34a6414774075c6fe33af071ea.jpg"
            ibb_img = self.load_image_from_url(ibb_url, (250, 250))
            self.ibb_label = ttk.Label(self.container, image=ibb_img)
            self.ibb_label.image = ibb_img
            self.ibb_label.pack(pady=10)
        except Exception as e:
            self.ibb_label = ttk.Label(self.container, text="Error loading IBB image")
            self.ibb_label.pack(pady=10)

        # Placeholder for YouTube profile pic
        self.yt_profile_label = ttk.Label(self.container)
        self.yt_profile_label.pack(pady=10)

        # Channel Name and ID
        ttk.Label(self.container, textvariable=self.channel_name_var, font=("Open Sans", 14, "bold")).pack(pady=5)
        ttk.Label(self.container, textvariable=self.channel_id_var, font=("Open Sans", 10)).pack(pady=2)

        # Stats Labels
        ttk.Label(self.container, textvariable=self.status, font=("Open Sans", 12, "bold")).pack(pady=5)
        ttk.Label(self.container, textvariable=self.viewer_count, font=("Open Sans", 12)).pack(pady=2)
        ttk.Label(self.container, textvariable=self.real_count, font=("Open Sans", 12)).pack(pady=2)
        ttk.Label(self.container, textvariable=self.bot_count, font=("Open Sans", 12)).pack(pady=2)
        ttk.Label(self.container, textvariable=self.ai_bot_count, font=("Open Sans", 12)).pack(pady=2)

        # Loading spinner vars
        self.loading = False
        self.loading_dots = 0

        # Start update threads
        threading.Thread(target=self.update_data_loop, daemon=True).start()
        self.animate_loading()

    def load_image_from_url(self, url, size):
        response = requests.get(url)
        img_data = response.content
        img = Image.open(BytesIO(img_data))
        img = img.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)

    def update_youtube_profile_image(self, url):
        try:
            profile_img = self.load_image_from_url(url, (100, 100))
            self.yt_profile_label.configure(image=profile_img)
            self.yt_profile_label.image = profile_img
        except Exception:
            self.yt_profile_label.configure(text="Error loading profile image")

    def animate_loading(self):
        if self.loading:
            self.loading_dots = (self.loading_dots + 1) % 4
            dots = '.' * self.loading_dots
            self.status.set(f"Checking{dots}")
        self.root.after(500, self.animate_loading)

    def update_data_loop(self):
        while True:
            try:
                self.loading = True

                channel_name, profile_url = get_channel_info(CHANNEL_ID)
                if channel_name:
                    self.channel_name_var.set(channel_name)
                else:
                    self.channel_name_var.set("Channel Name: N/A")

                self.channel_id_var.set(f"Channel ID: {CHANNEL_ID}")

                if profile_url:
                    self.update_youtube_profile_image(profile_url)
                else:
                    self.yt_profile_label.configure(text="Profile image unavailable")

                video_id = get_live_stream_id(CHANNEL_ID)
                if not video_id:
                    self.status.set("No active live stream.")
                    self.clear_stats()
                    self.loading = False
                    time.sleep(BOT_ESTIMATION_INTERVAL_SEC)
                    continue

                stats = get_stream_stats(video_id)
                if not stats or not stats.get('activeChatId'):
                    self.status.set("Live stream has no active chat.")
                    self.clear_stats()
                    self.loading = False
                    time.sleep(BOT_ESTIMATION_INTERVAL_SEC)
                    continue

                chat = get_chat_analysis(stats['activeChatId'], CHAT_COLLECTION_DURATION_SEC)
                est = estimate_viewers(stats['concurrentViewers'], chat)

                now_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_data = {
                    'timestamp': now_local,
                    'channelId': CHANNEL_ID,
                    'videoId': video_id,
                    'concurrentViewers': stats['concurrentViewers'],
                    **chat,
                    **est
                }
                log_to_file(log_data)

                self.viewer_count.set(f"Total Viewers: {stats['concurrentViewers']}")
                self.real_count.set(f"Estimated Real Viewers: {est['estimatedRealViewers']}")
                self.bot_count.set(f"Estimated Bots: {est['estimatedBotViewers']}")
                self.ai_bot_count.set(f"Detected AI-like Bots: {chat['detectedAiLikeBots']}")

                self.status.set(f"✅ Analysis complete ({now_local})")
                self.loading = False

            except Exception as e:
                self.status.set(f"Error: {e}")
                self.clear_stats()
                self.loading = False

            time.sleep(BOT_ESTIMATION_INTERVAL_SEC)

    def clear_stats(self):
        self.viewer_count.set("Total Viewers: N/A")
        self.real_count.set("Estimated Real Viewers: N/A")
        self.bot_count.set("Estimated Bots: N/A")
        self.ai_bot_count.set("Detected AI-like Bots: N/A")

if __name__ == "__main__":
    root = tk.Tk()
    app = BotDetectorGUI(root)
    root.mainloop()
