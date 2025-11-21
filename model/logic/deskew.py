from wand.image import Image
from wand.color import Color
from model.data.document import Document
from pathlib import Path


def deskew_image(in_file,out_file):
    try:
        with Image(filename=str(in_file)) as img:
            img.background_color = Color('transparent')
            img.deskew(0.40 * img.quantum_range)
            img.save(filename=str(out_file))
            return out_file
        
    except Exception as e:
       raise f"Error saving deskewed image: {in_file} to {out_file}: {e}"

def deskew_document(doc:Document):
    all_images_successful = True
    doc_directory = Path(doc.path)
    doc_directory.mkdir(parents=True, exist_ok=True)
    
    for image_id, image_task in doc.images.items():
        in_file = Path(image_task["original"])
        out_file = Path(image_task["processed"])

        try:
            deskew_image(in_file,out_file)
    
        except Exception as e:
            raise e

    return doc