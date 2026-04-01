from PyQt6.QtGui import QImage           
from wand.image import Image

def load_image(image_path) -> QImage:
    """Store the original pixmap and update the display."""
    try:

        with Image(filename=image_path) as img:
            
            img.format = 'rgba'
            
            blob_data = img.make_blob()
            
            qimage = QImage(
                blob_data,
                img.width,
                img.height,
                QImage.Format.Format_RGBA8888
            )
            return qimage.copy()

    except Exception as e:
        print(f"Wand Error: {e}")

def load_image_series(image_path_list) -> list:
    return [load_image(path) for path in image_path_list]