from pathlib import Path
import sys
import os
import configparser

def get_base_dir() -> Path:
    """Reliably gets the directory containing the app or source code."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

def get_app_paths(app_name: str) -> tuple[Path, Path]:
    """
    Returns (config_dir, data_dir) dynamically based on OS and Installation Mode.
    Linux strictly splits these; Windows and macOS bundle them together.
    """
    base_dir = get_base_dir()
    ini_path = base_dir / "install_mode.ini"
    mode = "CurrentUser" 

    if ini_path.exists():
        config = configparser.ConfigParser()
        config.read(ini_path)
        mode = config.get("Settings", "Mode", fallback="CurrentUser")
        
    if sys.platform == "win32":
        # Windows: Both Config and Data go to AppData/ProgramData
        base = Path(os.getenv('PROGRAMDATA', 'C:\\ProgramData')) / app_name if mode == "AllUsers" else Path(os.getenv('APPDATA')) / app_name
        return base, base
            
    elif sys.platform == "darwin": 
        # macOS: Both Config and Data go to Application Support
        base = Path("/Library/Application Support") / app_name if mode == "AllUsers" else Path.home() / "Library/Application Support" / app_name
        return base, base
            
    else: 
        # Linux: Strictly separates Config (/etc or .config) and Data (/var/lib or .local/share)
        if mode == "AllUsers":
            return Path("/etc") / app_name, Path("/var/lib") / app_name
        else:
            xdg_config = os.getenv('XDG_CONFIG_HOME', str(Path.home() / ".config"))
            xdg_data = os.getenv('XDG_DATA_HOME', str(Path.home() / ".local/share"))
            return Path(xdg_config) / app_name, Path(xdg_data) / app_name

def get_resources_dir() -> Path:
    """Safely resolves the resources folder, handling PyInstaller extraction."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as a compiled .exe: it lives in the temp extraction folder
        return Path(sys._MEIPASS) / "resources"
    else:
        # Running from source: it lives right next to this config file
        return Path(__file__).resolve().parent / "resources"


# --- APP CONSTANTS ---
APP_NAME = "ArchivePipeline"
DEV_MODE = Path('.dev').exists()
VERSION_STRING = '0.1.0'

# --- CORE PATHS ---
SRC_ROOT = Path(__file__).parent
RESOURCES_PATH = get_resources_dir()
CONFIG_DIR, DATA_DIR = get_app_paths(APP_NAME)

# --- CONFIGURATION FILES (.config) ---
LIVE_SETTINGS_FILE = CONFIG_DIR / "settings.json"
IA_CONFIG_PATH = CONFIG_DIR / "ia.ini"
DOCUMENT_SCHEMA_PATH = CONFIG_DIR / "document_schema.json"
FIELD_TYPES_PATH = CONFIG_DIR / "field_types.json"

# --- DATA FILES (.local/share) ---
DB_PATH = DATA_DIR / "archive_database.db"

# --- USER EXPORTS ---
DEFAULT_OUTPUT_DIR = Path.home() / "Documents" / f"{APP_NAME}_Output"

# --- MISC CONSTANTS ---
REQUIRED_METADATA = ["identifier", "title", "date", "mediatype"]

