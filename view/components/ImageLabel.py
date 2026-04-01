from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt

class ImageLabel(QLabel):
    """
    A custom QLabel that scales a QImage to fill the widget 
    while maintaining aspect ratio, converting to QPixmap JIT.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(1, 1) 
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName("imageLabel") 
        self._original_image = None

    def set_image(self, qimage: QImage):
        self._original_image = qimage
        self._update_display()
        
    def resizeEvent(self, event):
        """Handle window resizing."""
        self._update_display()
        super().resizeEvent(event)

    def _update_display(self):
        """Internal helper to scale and do JIT Pixmap conversion."""
        if not self._original_image:
            super().setPixmap(QPixmap())
            return
        else:
            scaled_image = self._original_image.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            super().setPixmap(QPixmap.fromImage(scaled_image))