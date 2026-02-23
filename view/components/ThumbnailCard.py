import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QStackedWidget, QLabel, QPushButton, QSplitter, 
    QListWidgetItem, QFrame, QFormLayout, QLineEdit, QDateEdit,
    QProgressBar, QComboBox, QGraphicsView, QGraphicsScene,QGridLayout,
    QScrollArea,QSizePolicy, QLayout
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QIcon, QFont, QColor, QCursor,QPixmap
from view.components.ImageLabel import ImageLabel

class ThumbnailCard(ImageLabel):
    clicked = pyqtSignal(str)

    def __init__(self, page_number, image_path=None):
        super().__init__()
        self.page_number = page_number
        self.is_selected = False
        
        self.setFixedSize(140, 180)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Styles
        self.default_style = """
            QFrame { background-color: white; border: 1px solid #d1d5da; border-radius: 6px; }
            QFrame:hover { border: 1px solid #0366d6; }
        """
        self.selected_style = """
            QFrame { background-color: #f0f8ff; border: 2px solid #0366d6; border-radius: 6px; }
        """
        self.setStyleSheet(self.default_style)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # --- 1. THE IMAGE LABEL ---
        self.image_lbl = QLabel()
        self.image_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_lbl.setStyleSheet("border: none; background: transparent;")
        
        # Load the image if path exists
        if image_path:
            self.setPixmap(image_path)
        else:
            self.image_lbl.setText("No Image") # Fallback
            
        layout.addWidget(self.image_lbl, 1)
        
        # --- 2. The Page Label ---
        self.text_lbl = QLabel(f"Page {page_number}")
        self.text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_lbl.setStyleSheet("border: none; font-weight: bold; color: #555;")
        self.text_lbl.setFont(QFont("Segoe UI", 9))
        layout.addWidget(self.text_lbl)
        
        self.setLayout(layout)

    def set_image(self, pixmap):
        """Loads and scales the image to fit the card."""
        self.setPixmap(pixmap)
        
        if not pixmap.isNull():
            # Scale it to fit the 120x130 area (approx size inside card margins)
            # KeepAspectRatio: Ensures document doesn't look stretched
            # SmoothTransformation: Prevents jagged edges
            scaled_pix = pixmap.scaled(
                120, 130,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_lbl.setPixmap(scaled_pix)
        else:
            self.image_lbl.setText("Err")