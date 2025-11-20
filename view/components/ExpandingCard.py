import sys
from PyQt6.QtCore import pyqtSignal, Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFrame, QLabel,
    QLineEdit, QCheckBox, QHBoxLayout, QSizePolicy
)


# --- This helper class is unchanged ---
class ClickableFrame(QFrame):
    """A QFrame that emits a 'clicked' signal when pressed."""
    clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setObjectName("clickable_header")
        self.setStyleSheet(self._get_style("default"))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        self.setStyleSheet(self._get_style("hover"))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(self._get_style("default"))
        super().leaveEvent(event)

    def _get_style(self, state: str, is_open: bool = False) -> str:
        if state == "hover":
            bg_color = "#e9e9e9"
            border_color = "#ccc"
        else: # default
            bg_color = "#f7f7f7"
            border_color = "#ddd"

        if is_open:
            radius = "4px 4px 0 0"
        else:
            radius = "4px"
            
        return f"""
            QFrame#clickable_header {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: {radius};
            }}
        """

    def set_open_style(self, is_open: bool):
        self.setStyleSheet(self._get_style("default", is_open))


# --- This class has been updated ---
class ExpandingWidget(QWidget):
    """
    A collapsible/expandable widget with a clickable header.
    Summary widgets in the header are hidden when expanded.
    """
    def __init__(self, title: str = "Title", parent: QWidget | None = None):
        super().__init__(parent)
        
        self.is_expanded = False
        
        # --- NEW: List to hold summary widgets ---
        self.summary_widgets = [] 

        # --- Components ---
        self.header_frame = ClickableFrame()
        self.arrow_label = QLabel("\u25B6")  # ►
        self.arrow_label.setFixedWidth(20)
        self.arrow_label.setStyleSheet("font-weight: bold;")
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 11pt;")

        self.summary_layout = QHBoxLayout()
        self.summary_layout.setContentsMargins(0, 0, 0, 0)
        self.summary_layout.setSpacing(5)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 8, 8, 8)
        header_layout.setSpacing(8)
        header_layout.addWidget(self.arrow_label)
        header_layout.addWidget(self.title_label)
        header_layout.addLayout(self.summary_layout)
        header_layout.addStretch()
        self.header_frame.setLayout(header_layout)

        self.content_area = QFrame()
        self.content_area.setStyleSheet("""
            QFrame { 
                background-color: #fafafa; 
                border: 1px solid #ccc;
                border-top: none; 
                border-radius: 0 0 4px 4px;
                margin-top: -1px;
            }
        """)
        self.content_area.setMaximumHeight(0)
        self.content_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(8) # Added a bit more spacing
        self.content_area.setLayout(self.content_layout)

        self.animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.header_frame)
        main_layout.addWidget(self.content_area)
        self.setLayout(main_layout)

        self.header_frame.clicked.connect(self.toggle)

    def toggle(self):
        """Handles the expand/collapse animation and summary visibility."""
        
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            # --- EXPAND ---
            self.arrow_label.setText("\u25BC")  # ▼
            self.header_frame.set_open_style(is_open=True)
            
            # --- NEW: Hide summary widgets ---
            for w in self.summary_widgets:
                w.setVisible(False)
            
            self.animation.setStartValue(0)
            full_height = self.content_layout.sizeHint().height()
            self.animation.setEndValue(full_height)
        else:
            # --- COLLAPSE ---
            self.arrow_label.setText("\u25B6")  # ►
            self.header_frame.set_open_style(is_open=False)
            
            # --- NEW: Show summary widgets ---
            for w in self.summary_widgets:
                w.setVisible(True)
                
            self.animation.setStartValue(self.content_area.height())
            self.animation.setEndValue(0)
            
        self.animation.start()

    def add_summary_widget(self, widget: QWidget):
        """
        Adds a widget to the summary area.
        This widget will be hidden when the card is expanded.
        """
        self.summary_layout.addWidget(widget)
        # --- NEW: Add to our tracking list ---
        self.summary_widgets.append(widget)

    def add_detail_widget(self, widget: QWidget):
        """Adds a widget to the (collapsible) detail area."""
        self.content_layout.addWidget(widget)


# --- New Example: Service Status Indicators ---

class ExampleWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Service Status Demo")
        self.setGeometry(300, 300, 400, 200)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # --- Create the Service Status Widget ---
        service_widget = ExpandingWidget(title="Service Status")

        # --- 1. Add Summary Widgets (the row of indicators) ---
        # These will be hidden when expanded
        service_widget.add_summary_widget(self.create_indicator("green"))
        service_widget.add_summary_widget(self.create_indicator("red"))
        service_widget.add_summary_widget(self.create_indicator("orange"))

        # --- 2. Add Detail Widgets (the vertical stack) ---
        # These are only visible when expanded
        service_widget.add_detail_widget(
            self.create_detail_row("green", "Database", "Online")
        )
        service_widget.add_detail_widget(
            self.create_detail_row("red", "API", "Offline - Error 503")
        )
        service_widget.add_detail_widget(
            self.create_detail_row("orange", "Web App", "High Latency")
        )

        main_layout.addWidget(service_widget)
        main_layout.addStretch()

    def create_indicator(self, color: str) -> QLabel:
        """Helper to create a simple colored circle label."""
        indicator = QLabel("●") # A unicode circle character
        indicator.setStyleSheet(f"color: {color}; font-size: 16pt;")
        return indicator

    def create_detail_row(self, color: str, name: str, status: str) -> QWidget:
        """Helper to create a full row for the detail view."""
        # Use a QFrame as a container for the row
        row_widget = QFrame()
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)

        # 1. The Indicator
        indicator = self.create_indicator(color)
        
        # 2. The Name
        name_label = QLabel(name)
        name_label.setStyleSheet("font-weight: bold;")

        # 3. The Status
        status_label = QLabel(status)
        
        row_layout.addWidget(indicator)
        row_layout.addWidget(name_label)
        row_layout.addStretch()
        row_layout.addWidget(status_label)
        
        row_widget.setLayout(row_layout)
        return row_widget


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExampleWindow()
    window.show()
    sys.exit(app.exec())