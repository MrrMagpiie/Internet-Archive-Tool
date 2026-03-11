import json
from config import LIVE_SETTINGS_FILE

class SettingsManager:
    def __init__(self):
        self._data = {}

    def load(self):
        """Reads the JSON file from the hard drive into memory."""
        with open(LIVE_SETTINGS_FILE, 'r') as f:
            self._data = json.load(f)

    def get(self, key: str, default=None):
        """Retrieves a setting. Returns 'default' if the key is missing."""
        return self._data.get(key, default)

    def get_all(self):
        return self._data

    def set(self, key: str, value):
        """Updates a setting in memory."""
        self._data[key] = value

    def save(self):
        """Writes the current memory state back to the hard drive."""
        with open(LIVE_SETTINGS_FILE, 'w') as f:
            json.dump(self._data, f, indent=4)

app_settings = SettingsManager()