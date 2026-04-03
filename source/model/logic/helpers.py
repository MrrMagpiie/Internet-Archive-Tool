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

def load_metadata_formats():
    with open(DOCUMENT_SCHEMA_PATH,'r') as f:
            return json.load(f)

