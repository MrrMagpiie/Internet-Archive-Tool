import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QImage
from view.components.ImageLabel import ImageLabel 

class ThumbnailCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, page_number, qimage=None):
        super().__init__()
        self.page_number = page_number
        self.is_selected = False
        
        self.setFixedSize(140, 180)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        self.setObjectName("thumbnailCard")
        self.setProperty("selected", False)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        self.image_view = ImageLabel()
        
        if qimage:
            self.image_view.set_image(qimage)
        else:
            self.image_view.setText("No Image")
            
        layout.addWidget(self.image_view, 1)
        
        self.text_lbl = QLabel(f"Page {page_number}")
        self.text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_lbl.setObjectName("thumbnailPageLabel")
        
        layout.addWidget(self.text_lbl)
        
        self.setLayout(layout)

    def set_image(self, qimage: QImage):
        """Pass-through method to update the internal ImageLabel."""
        self.image_view.set_image(qimage)

    def set_selected(self, selected: bool):
        """Updates the state and forces the QSS to re-evaluate."""
        self.is_selected = selected
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(str(self.page_number))
        super().mousePressEvent(event)