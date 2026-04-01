import qtawesome as qta
from config import DEV_MODE
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QProgressBar,QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QCursor
from model.data.document import Document
from model.service.signals import DatabaseTicket
from model.service.SessionManager import SessionManager



stages = {
    0: (10, 'Discovered'),
    1: (50, 'Needs Metadata'),
    2: (80, 'Needs Review'),
    3: (100, 'Uploaded')
}

class DocumentCard(QFrame):
    clicked = pyqtSignal(Document, int)
    def __init__(self, document: Document, stage: int):
        super().__init__()
        self.setObjectName("docuCard")
        self.doc = document
        self.title = self.doc.doc_id
        self.stage = stage 
        self.prog, self.status = stages[stage]
        
        # 1. Base Card Setup
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedSize(280, 160)
         # Link to QSS
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout()
        
        # 2. Icon/Color Indicator (Top Strip)
        self.status_strip = QFrame()
        self.status_strip.setFixedHeight(4)
        # Dynamically name it so QSS can color it based on the stage
        self.status_strip.setObjectName(f"statusStrip_{stage}") 
        layout.addWidget(self.status_strip)
        
        # 3. Title
        self.lbl_title = QLabel(self.title)
        self.lbl_title.setObjectName("cardTitle")
        layout.addWidget(self.lbl_title)
        
        # 4. Subtitle
        self.lbl_subtitle = QLabel(self.status)
        self.lbl_subtitle.setObjectName("cardSubtitle")
        layout.addWidget(self.lbl_subtitle)
        
        layout.addStretch()
        
        # 5. Progress Bar
        self.pbar = QProgressBar()
        self.pbar.setValue(self.prog)
        self.pbar.setTextVisible(False)
        self.pbar.setFixedHeight(6)
        self.pbar.setObjectName(f"cardProgressBar_{stage}")
        layout.addWidget(self.pbar)
        
        self.setLayout(layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.doc, self.stage)
            
        super().mousePressEvent(event)

class ActionCard(QFrame):
    clicked = pyqtSignal()
    
    def __init__(self,icon,text):
        super().__init__()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setObjectName("actionCard")
        
        # Center the content
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # The Plus Icon
        icon_lbl = QLabel(icon)
        icon_lbl.setObjectName("actionCardIcon") 
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # The Text
        text_lbl = QLabel(text)
        text_lbl.setObjectName("actionCardText") 
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl)
        
        self.setLayout(layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

