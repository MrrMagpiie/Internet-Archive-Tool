from PyQt6.QtGui import QImage           
from wand.image import Image
from PyQt6.QtCore import QRunnable, QThreadPool

class ImageLoadTask(QRunnable):
    def __init__(self, image_path, signals):
        super().__init__()
        self.image_path = image_path
        self.signals = signals

    def run(self):
        if self.signals.is_cancelled():
            return
            
        try:
            qimage = load_image(self.image_path)
            
            if not self.signals.is_cancelled():
                self.signals.data.emit(qimage, self.signals.job_id)
        except Exception as e:
            self.signals.error.emit(e, self.signals.job_id)

def load_image(image_path) -> QImage:
    """takes image path and returns QImage."""
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