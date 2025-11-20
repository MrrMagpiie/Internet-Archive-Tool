import sys
from PyQt6.QtCore import pyqtSignal, Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFrame, QLabel,
    QLineEdit, QCheckBox, QHBoxLayout, QSizePolicy
)

class ClickableFrame(QFrame):
    """A QFrame that emits a 'clicked' signal when pressed."""
    clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Set a base style for the header
        self.setObjectName("clickable_header")
        self.setStyleSheet(self._get_style("default"))

    def mousePressEvent(self, event):
        """Emit the clicked signal on a left-button press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        """Handle mouse hover enter."""
        self.setStyleSheet(self._get_style("hover"))
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse hover leave."""
        self.setStyleSheet(self._get_style("default"))
        super().leaveEvent(event)

    def _get_style(self, state: str, is_open: bool = False) -> str:
        """Helper to get the correct stylesheet string."""
        if state == "hover":
            bg_color = "#e9e9e9"
            border_color = "#ccc"
        else: # default
            bg_color = "#f7f7f7"
            border_color = "#ddd"

        if is_open:
            radius = "4px 4px 0 0" # Only round top corners
        else:
            radius = "4px" # Round all corners
            
        return f"""
            QFrame#clickable_header {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: {radius};
            }}
        """

    def set_open_style(self, is_open: bool):
        """Updates the border-radius based on the open/closed state."""
        self.setStyleSheet(self._get_style("default", is_open))

