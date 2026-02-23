

from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from wand.image import Image as WandImage 
from PyQt6.QtGui import QImage, QPixmap            

def load_image(image_path) -> QPixmap:
    """Store the original pixmap and update the display."""
    try:
        with WandImage(filename=image_path) as img:
            
            img.format = 'rgba'
            
            blob_data = img.make_blob()
            
            qimage = QImage(
                blob_data,
                img.width,
                img.height,
                QImage.Format.Format_RGBA8888
            )
            pixmap = QPixmap.fromImage(qimage)
            return pixmap

    except Exception as e:
        print(f"Wand Error: {e}")

def load_image_series(image_path_list) -> list:
    image_list = []
    for image_path in image_path_list:
        image_list.append(load_image(image_path))

    return image_list