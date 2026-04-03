from pathlib import Path
from model.data.document import Document
from model.settings_manager import app_settings

from pathlib import Path

image_formats = ['.tif', '.tiff', '.jpg', '.jpeg', '.png']

def discover_images(directory) -> list:
    path = Path(directory)
    return [p for p in path.iterdir() if p.suffix.lower() in image_formats]

def images_to_documents(image_list) -> dict:
    documents = {}
    for file in image_list:
        try:
            parts = file.stem.split()
            order = "001"
            if len(parts) > 1:
                order = "".join(char for char in parts.pop() if char.isdigit())
            doc_id = "_".join(parts)
            image_id = file.name

            if doc_id in documents.keys():
                documents[doc_id].append((file,image_id,order))
            else:
                documents[doc_id] = [(file,image_id,order)]
    
        except Exception as e:
            raise 
    return documents
