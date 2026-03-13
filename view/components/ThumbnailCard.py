import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from view.components.ImageLabel import ImageLabel

# FIXED: Inherit from QFrame so it acts as a proper styled container
class ThumbnailCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, page_number, pixmap=None):
        super().__init__()
        self.page_number = page_number
        self.is_selected = False
        
        self.setFixedSize(140, 180)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # 1. NEW: Assign standard ID for QSS
        self.setObjectName("thumbnailCard")
        
        # 2. NEW: Assign a dynamic property for the selected state
        self.setProperty("selected", False)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # --- 1. THE IMAGE LABEL ---
        # FIXED: Use your custom ImageLabel widget here as a child!
        self.image_view = ImageLabel()
        
        if pixmap:
            self.image_view.set_pixmap(pixmap)
        else:
            self.image_view.setText("No Image")
            
        layout.addWidget(self.image_view, 1)
        
        # --- 2. The Page Label ---
        self.text_lbl = QLabel(f"Page {page_number}")
        self.text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_lbl.setObjectName("thumbnailPageLabel") # NEW: Hook for QSS
        
        layout.addWidget(self.text_lbl)
        
        self.setLayout(layout)

    def set_pixmap(self, pixmap):
        """Pass-through method to update the internal ImageLabel."""
        self.image_view.set_pixmap(pixmap)

    def set_selected(self, selected: bool):
        """Updates the state and forces the QSS to re-evaluate."""
        self.is_selected = selected
        
        # Update the dynamic property
        self.setProperty("selected", selected)
        
        # Tell the PyQt styling engine to refresh this widget's appearance
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(str(self.page_number))
        super().mousePressEvent(event)