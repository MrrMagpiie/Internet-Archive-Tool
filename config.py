# In config.py
from pathlib import Path
import json

SRC_ROOT = Path(__file__).parent
PROJECT_ROOT = SRC_ROOT.parent
RESOURCES_PATH = SRC_ROOT / "resources"
SETTINGS_PATH = RESOURCES_PATH / "settings.json"

REQUIRED_METADATA = [
    "identifier", "title", "date", "mediatype"
]

with open(SETTINGS_PATH,'r') as f:
    user_config = json.load(f)

DEFAULT_OUTPUT_DIR = Path(user_config.get('DEFAULT_OUTPUT_DIR'))
DB_PATH = Path(user_config.get('DATABASE_PATH'))
ADMIN_UPLOAD = user_config.get('ADMIN_UPLOAD')
AUTO_DESKEW = user_config.get('AUTO_DESKEW')
