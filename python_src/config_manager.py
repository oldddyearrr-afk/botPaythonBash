# config_manager.py - إدارة الإعدادات
import json
import os
import threading

DEFAULT_CONFIG = {
    "BOT_TOKEN": os.environ.get("BOT_TOKEN", ""),
    "YOUR_USER_ID": os.environ.get("YOUR_USER_ID", ""),
    "CHANNEL_ID": os.environ.get("CHANNEL_ID", ""),
    "SOURCE_URL": os.environ.get("SOURCE_URL", ""),
    "CLIP_SECONDS": 14,
    "SLEEP_BETWEEN": 0,
    "BOTTOM_WATERMARK_TEXT": "Telegram | @media_ayham",
    "BOTTOM_WATERMARK_ENABLED": True,
    "BUFFER_SIZE": 5,
    "KEYFRAME_INTERVAL": 2
}

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.lock = threading.Lock()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    return {**DEFAULT_CONFIG, **loaded}
            except:
                pass
        return DEFAULT_CONFIG.copy()

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        with self.lock:
            self.config[key] = value

    def validate_required_vars(self):
        required_vars = ["BOT_TOKEN", "YOUR_USER_ID", "CHANNEL_ID", "SOURCE_URL"]
        missing_vars = [var for var in required_vars if not self.get(var)]
        
        if missing_vars:
            print("❌ المتغيرات المطلوبة:")
            for var in missing_vars:
                print(f"   {var}")
            return False
        return True
