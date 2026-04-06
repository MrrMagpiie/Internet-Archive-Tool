import json
import keyring
from config import LIVE_SETTINGS_FILE, APP_NAME

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

    def set_secret(self, service: str, username: str, password: str):
        """Securely stores a password in the OS Keyring."""
        keyring.set_password(f"{APP_NAME}_{service}", username, password)

    def get_secret(self, service: str, username: str) -> str:
        """Retrieves a password from the OS Keyring."""
        return keyring.get_password(f"{APP_NAME}_{service}", username)
        
    def set_database_config(self, db_config: dict):
        """Convenience method to save database configuration, including secrets."""
        self.set("DB_PROVIDER", db_config.get("provider"))
        self.set("DB_TYPE", db_config.get("type"))
        
        if db_config.get("type") == "file":
            self.set("DB_PATH", db_config.get("path"))
        else:
            self.set("DB_HOST", db_config.get("host"))
            self.set("DB_PORT", db_config.get("port"))
            self.set("DB_NAME", db_config.get("database"))
            self.set("DB_USER", db_config.get("user"))
            
            # Store the sensitive password natively using our helper
            self.set_secret("Database", db_config["user"], db_config["password"])
            
        self.save()

    def get_database_config(self) -> dict:
        """Retrieves the database configuration, fetching secrets if necessary."""
        db_type = self.get("DB_TYPE")
        if not db_type:
            return {}
            
        config = {
            "provider": self.get("DB_PROVIDER"),
            "type": db_type
        }
        
        if db_type == "file":
            config["path"] = self.get("DB_PATH")
        else:
            config["host"] = self.get("DB_HOST")
            config["port"] = self.get("DB_PORT")
            config["database"] = self.get("DB_NAME")
            config["user"] = self.get("DB_USER")
            
            # Fetch the sensitive password natively
            config["password"] = self.get_secret("Database", config["user"])
            
        return config

app_settings = SettingsManager()