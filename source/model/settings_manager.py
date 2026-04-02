import json
from config import LIVE_SETTINGS_FILE

class SettingsManager:
    def __init__(self):
        self._data = {}

    def load(self):
        """Reads the JSON file from the hard drive into memory safely."""
        if not LIVE_SETTINGS_FILE.exists():
            print(f"Warning: Settings file not found at {LIVE_SETTINGS_FILE}. Using empty defaults.")
            self._data = {}
            return

        try:
            with open(LIVE_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        except json.JSONDecodeError:
            print(f"CRITICAL: Settings file {LIVE_SETTINGS_FILE} is corrupted! Falling back to empty defaults.")
            self._data = {}
        except Exception as e:
            print(f"Error loading settings: {e}")
            self._data = {}

    def get(self, key: str, default=None):
        """Retrieves a setting. Returns 'default' if the key is missing."""
        return self._data.get(key, default)

    def get_all(self):
        return self._data

    def set(self, key: str, value):
        """Updates a setting in memory."""
        self._data[key] = value

    def save(self):
        """Writes the current memory state back to the hard drive safely."""
        LIVE_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(LIVE_SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, indent=4)

app_settings = SettingsManager()