
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import  Qt

class ImageLabel(QLabel):
    """A custom QLabel to display a pixmap with a preserved aspect ratio."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(1, 1)
        self.setPixmap(QPixmap()) # Start with an empty pixmap

    def setPixmap(self, pixmap):
        # Store the original pixmap to use for scaling
        self._pixmap = pixmap
        # Trigger a resize event to scale the pixmap
        self.resizeEvent(None)

    def resizeEvent(self, event):
        # This method is called whenever the label is resized.
        # We scale the original pixmap to fit the label's current size.
        if not self._pixmap or self._pixmap.isNull():
            return

        # Scale the pixmap, keeping the aspect ratio.
        # The result will be the largest pixmap that fits within the label's bounds.
        scaled_pixmap = self._pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation  # For better image quality
        )
        # Call the original QLabel's setPixmap method to display the scaled image.
        super().setPixmap(scaled_pixmap)
