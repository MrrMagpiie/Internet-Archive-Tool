import os
import sys
import shutil
from pathlib import Path
from config import USER_RESOURCES_DIR, LIVE_SETTINGS_FILE, APPDATA_DIR, DB_PATH, DOCUMENT_SCHEMA_PATH, FIELD_TYPES_PATH, DEFAULT_OUTPUT_DIR
from model.settings_manager import app_settings



def init_app_environment():
    """Action function: Physically builds the required file system."""
    
    # 1. Create the directories
    USER_RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # 2. Copy the template if needed
    if not LIVE_SETTINGS_FILE.exists():
        if hasattr(sys, '_MEIPASS'):
            setting_template_path = Path(sys._MEIPASS) / "resources" / "default_settings.json"

        else:
            settings_template_path = Path("resources") / "default_settings.json"
            
        if settings_template_path.exists():
            shutil.copy(settings_template_path, LIVE_SETTINGS_FILE)
            print("Environment initialized: Default settings copied.")
            
    if not DOCUMENT_SCHEMA_PATH.exists():
        if hasattr(sys, '_MEIPASS'):
            schema_template_path = Path(sys._MEIPASS) / "resources" / "default_schema.json"
        else:
            schema_template_path = Path("resources") / "default_schema.json"
            
        if schema_template_path.exists():
            shutil.copy(schema_template_path, DOCUMENT_SCHEMA_PATH)
            print("Environment initialized: Default schema copied.")
    
    if not FIELD_TYPES_PATH.exists():
        if hasattr(sys, '_MEIPASS'):
            field_template_path = Path(sys._MEIPASS) / "resources" / "default_field_types.json"
        else:
            field_template_path = Path("resources") / "default_field_types.json"
            
        if field_template_path.exists():
            shutil.copy(field_template_path, FIELD_TYPES_PATH)
            print("Environment initialized: Default field types copied.")


    app_settings.load()
    app_settings.set('DEFAULT_OUTPUT_DIR',str(DEFAULT_OUTPUT_DIR))
    app_settings.save()