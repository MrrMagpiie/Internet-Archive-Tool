import sys
from PyQt6.QtCore import pyqtSignal, Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFrame, QLabel,
    QHBoxLayout, QSizePolicy
)

class ExpandingWidget(QWidget):
    """
    A collapsible/expandable widget with a clickable header.
    Summary widgets in the header are hidden when expanded.
    """
    def __init__(self, title: str = "Title", parent: QWidget | None = None):
        super().__init__(parent)
        
        self.is_expanded = False
        self.summary_widgets = [] 

        # --- Components ---
        self.header_frame = ClickableFrame()
        
        self.arrow_label = QLabel("\u25B6")  # ►
        self.arrow_label.setFixedWidth(20)
        self.arrow_label.setObjectName("ExpandingWidget_arrow")
        
        self.title_label = QLabel(title)
        self.title_label.setObjectName("ExpandingWidget_title")

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
        self.content_area.setObjectName("ExpandingWidget_content")
        self.content_area.setMaximumHeight(0)
        self.content_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(8) 
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
            self.header_frame.set_open_state(True)
            
            for w in self.summary_widgets:
                w.setVisible(False)
            
            self.animation.setStartValue(0)
            full_height = self.content_layout.sizeHint().height()
            self.animation.setEndValue(full_height)
        else:
            # --- COLLAPSE ---
            self.arrow_label.setText("\u25B6")  # ►
            self.header_frame.set_open_state(False)
            
            for w in self.summary_widgets:
                w.setVisible(True)
                
            self.animation.setStartValue(self.content_area.height())
            self.animation.setEndValue(0)
            
        self.animation.start()

    def add_summary_widget(self, widget: QWidget):
        self.summary_layout.addWidget(widget)
        self.summary_widgets.append(widget)

    def add_detail_widget(self, widget: QWidget):
        self.content_layout.addWidget(widget)