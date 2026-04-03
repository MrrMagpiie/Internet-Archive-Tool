import shutil
from config import (
    LIVE_SETTINGS_FILE, DOCUMENT_SCHEMA_PATH, FIELD_TYPES_PATH, 
    DEFAULT_OUTPUT_DIR, DATA_DIR, CONFIG_DIR, RESOURCES_PATH
)

def init_app_environment():
    """Action function: Physically builds the required file system."""
    try:    
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Map the internal template files to their live destinations
        file_mappings = {
            "default_settings.json": LIVE_SETTINGS_FILE,
            "default_schema.json": DOCUMENT_SCHEMA_PATH,
            "default_field_types.json": FIELD_TYPES_PATH
        }

        # Loop through and copy any missing files
        for template_name, live_path in file_mappings.items():
            if not live_path.exists():
                # config.py guarantees this path is correct!
                template_path = RESOURCES_PATH / template_name 
                
                if template_path.exists():
                    shutil.copy(template_path, live_path)
                    print(f"Environment initialized: Copied {template_name} -> {live_path.name}")
                else:
                    print(f"CRITICAL WARNING: Base template '{template_path}' is missing!")

        # Load and verify core settings
        from model.settings_manager import app_settings
        app_settings.load()
        app_settings.set('DEFAULT_OUTPUT_DIR', str(DEFAULT_OUTPUT_DIR))
        app_settings.save()
    except PermissionError:
        print(f"FATAL: No write access to {CONFIG_DIR}. Please run as Administrator or check permissions.")
        sys.exit(1)