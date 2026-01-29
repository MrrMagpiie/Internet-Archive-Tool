from PyQt6.QtWidgets import QLabel, QSizePolicy
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from wand.image import Image as WandImage 
from PyQt6.QtGui import QImage, QPixmap

from pathlib import Path

class ImageLabel(QLabel):
    """
    A custom QLabel that scales its pixmap to fill the widget 
    while maintaining aspect ratio.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        #self.setStyleSheet("border: 2px solid red; background-color: yellow;") #flag foor debugging
        self.setMinimumSize(1, 1) 
        self.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self._pixmap = None

    def setPixmap(self, image_path: Path):
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
        except Exception as e:
            print(f"Wand Error: {e}")
            self.image_label.setText("Error Loading Image")
        
        self._pixmap = QPixmap.fromImage(qimage)
        self._update_display()

    def resizeEvent(self, event):
        """Handle window resizing."""
        self._update_display()
        super().resizeEvent(event)

    def _update_display(self):
        """Internal helper to scale and set the pixmap."""
        if not self._pixmap or self._pixmap.isNull():
            super().setPixmap(QPixmap())
            return
        if not self._pixmap.isNull():
            scaled_pixmap = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            super().setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("Err")
            

    