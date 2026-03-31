import qdarktheme
import darkdetect
from pathlib import Path
from model.settings_manager import app_settings
from view.theme import LIGHT_PALETTE, DARK_PALETTE
from config import RESOURCES_PATH, DOCUMENT_SCHEMA_PATH
import json

def clear_layout(layout):
    """
    Recursively removes all widgets and nested layouts from a given layout.
    """
    if layout is None:
        return

    while layout.count():
        item = layout.takeAt(0)
        if item.widget() is not None:
            item.widget().deleteLater()      
        elif item.layout() is not None:
            clear_layout(item.layout())
def setup_theme(theme_choice = None):
    """
    Resolves the theme choice, compiles the custom QSS, 
    and applies it to the application.
    """
    
    if not theme_choice: theme_choice = app_settings.get("THEME", "auto")

    # 1. Resolve "auto" to explicitly "dark" or "light"
    if theme_choice == "auto":
        # darkdetect returns 'Dark' or 'Light' based on the OS settings
        os_theme = darkdetect.theme()
        resolved_theme = os_theme.lower() if os_theme else "dark" # Fallback to dark
    else:
        resolved_theme = theme_choice

    # 2. Pick the correct dictionary
    palette = DARK_PALETTE if resolved_theme == "dark" else LIGHT_PALETTE
    
    # 3. Read your raw stylesheet
    with open(RESOURCES_PATH / "style.qss", "r") as f:
        raw_qss = f.read()
        
    # 4. Compile: Swap every {{variable}} with its hex code
    for var_name, hex_code in palette.items():
        raw_qss = raw_qss.replace(var_name, hex_code)
        
    # 5. Apply the fully compiled string to the application
    qdarktheme.setup_theme(
        theme=resolved_theme, 
        additional_qss=raw_qss
    )