import sys
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QWidget, QFrame
class ClickableFrame(QFrame):
    """A QFrame that emits a 'clicked' signal when pressed."""
    clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # 1. Assign the global ID for the stylesheet
        self.setObjectName("clickable_header")
        
        # 2. Set an initial custom property for the QSS to read
        self.setProperty("isOpen", False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def set_open_state(self, is_open: bool):
        """Updates the property and forces the stylesheet to refresh."""
        self.setProperty("isOpen", is_open)
        
        # When changing dynamic properties, you must tell Qt to unpolish and 
        # repolish the widget so it grabs the new CSS rules.
        self.style().unpolish(self)
        self.style().polish(self)