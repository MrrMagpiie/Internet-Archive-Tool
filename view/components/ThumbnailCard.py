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

    def __init__(self, page_number, pixmap=None):
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
        if pixmap:
            self.set_pixmap(pixmap)
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


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(str(self.page_number))
        super().mousePressEvent(event)

 