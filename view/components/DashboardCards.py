import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QStackedWidget, QLabel, QPushButton, QSplitter, 
    QListWidgetItem, QFrame, QFormLayout, QLineEdit, QDateEdit,
    QProgressBar, QComboBox, QGraphicsView, QGraphicsScene,QGridLayout,
    QScrollArea,QSizePolicy, QLayout
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QIcon, QFont, QColor, QCursor
from model.data.document import Document

stages = {
    0:(10,"#0969da",'Discovered'),
    1:(50, "#d29922",'Needs Metadata'),
    2:(100,"#2da44e",'Needs Review'),
}

class DocumentCard(QFrame):
    clicked = pyqtSignal(Document,int)
    def __init__(self, document: Document,stage: int):
        super().__init__()
        self.doc = document
        self.title = self.doc.doc_id
        self.stage = stage 
        self.prog,self.color,self.status = stages[stage]
        
        
        # Style the Card to look like a distinct container
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet(f"""
            DocumentCard {{
                background-color: white;
                border: 1px solid #e1e4e8;
                border-radius: 8px;
            }}
            DocumentCard:hover {{
                border: 1px solid #0366d6;
                background-color: #f6f8fa;
            }}
        """)
        
        # Layout inside the card
        layout = QVBoxLayout()
        
        # Icon/Color Indicator (Top Strip)
        status_strip = QFrame()
        status_strip.setFixedHeight(4)
        status_strip.setStyleSheet(f"background-color: {self.color}; border-radius: 2px;")
        layout.addWidget(status_strip)
        
        # Title
        lbl_title = QLabel(self.title)
        lbl_title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl_title.setStyleSheet("border: none; background: transparent;") # Reset style
        layout.addWidget(lbl_title)
        
        # Subtitle (e.g. "Status: Processing")
        lbl_subtitle = QLabel(self.status)
        lbl_subtitle.setStyleSheet("color: #586069; border: none; background: transparent;")
        layout.addWidget(lbl_subtitle)
        
        # Spacer to push progress bar to bottom
        layout.addStretch()
        
        # Progress Bar
        pbar = QProgressBar()
        pbar.setValue(self.prog)
        pbar.setTextVisible(False)
        pbar.setFixedHeight(6)
        pbar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: #eaeaea;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {self.color};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(pbar)
        
        self.setLayout(layout)
        
        # Fix the size of the card
        self.setFixedSize(280, 160)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    # Capture the mouse click
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Emit the signal with this card's title
            print(f'{self.title} Emit')
            self.clicked.emit(self.doc,self.stage)
            
            
        # Standard event processing
        super().mousePressEvent(event)

class ActionCard(QFrame):
    def __init__(self,title,icon_text,description):
        super().__init__()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) 
        self.setObjectName("actionCardFrame") 

        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.icon_label = QLabel(icon_text)
        self.icon_label.setObjectName("cardIconLabel")
        layout.addWidget(self.icon_label)
        

        text_layout = QVBoxLayout(self)
        # Title: Font size determined dynamically
        self.title_label = QLabel(f"<span id='cardTitleText'>{title}</span>") 
        self.title_label.setObjectName("cardTitleLabel")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding) 
        text_layout.addWidget(self.title_label)
        layout.addSpacing(3)

        # Description: Font size determined dynamically
        self.desc_label = QLabel(f"<span id='cardDescText'>{description}</span>")
        self.desc_label.setWordWrap(True)
        self.desc_label.setObjectName("cardDescLabel")
        self.desc_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        text_layout.addWidget(self.desc_label)
        layout.addLayout(text_layout)
        
        
        self.setLayout(layout)
