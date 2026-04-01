from pathlib import Path
import json
import sys
import os




def get_app_data_dir(app_name: str) -> Path:
    """Dynamically resolves the correct user-data folder based on the OS."""
    home = Path.home()
    
    if sys.platform == "win32":
        return Path(os.getenv('APPDATA')) / app_name
        
    elif sys.platform == "darwin": # macOS
        return home / "Library" / "Application Support" / app_name
        
    else: 
        # Linux standard (uses XDG_CONFIG_HOME, defaults to ~/.config)
        xdg_config = os.getenv('XDG_CONFIG_HOME', str(home / ".config"))
        return Path(xdg_config) / app_name


APP_NAME = "ArchivePipeline"
DEV_MODE = Path('.dev').exists()

SRC_ROOT = Path(__file__).parent
RESOURCES_PATH = SRC_ROOT / "resources"

APPDATA_DIR = get_app_data_dir(APP_NAME)
USER_RESOURCES_DIR = APPDATA_DIR / "user_resources"
DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / "ArchivePipeline_Output"
LIVE_SETTINGS_FILE = USER_RESOURCES_DIR / "settings.json"
IA_CONFIG_PATH = USER_RESOURCES_DIR / "ia.ini"
DOCUMENT_SCHEMA_PATH = USER_RESOURCES_DIR / "document_schema.json"
FIELD_TYPES_PATH = USER_RESOURCES_DIR / "field_types.json"

DB_PATH = APPDATA_DIR / "database" / "archive_database.db"
VERSION_STRING = '0.1.0'




REQUIRED_METADATA = [
    "identifier", "title", "date", "mediatype"
]