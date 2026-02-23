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

    def setPixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
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
            

    