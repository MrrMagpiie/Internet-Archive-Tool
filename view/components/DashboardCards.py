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
    delete_requested = pyqtSignal(Document,QObject)
    remove_requested = pyqtSignal(Document,QObject)
    
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

    def contextMenuEvent(self, event):
        """Automatically triggered when the user right-clicks the card."""
        if not SessionManager.is_admin():
            return
        
        context_menu = QMenu(self)
        
        remove_action = context_menu.addAction("Remove Document")
        delete_action = context_menu.addAction("Delete Document")
        if DEV_MODE:
            dev_action = context_menu.addAction('Print Document')
        
        trash_icon = qta.icon('fa5s.trash-alt', color='#d73a49') 
        delete_action.setIcon(trash_icon)
        
        remove_icon = qta.icon('mdi6.database-minus-outline', color='#d73a49')
        remove_action.setIcon(remove_icon)
        
        clicked_action = context_menu.exec(self.mapToGlobal(event.pos()))
        
        if clicked_action == delete_action:
            self._confirm_deletion()
        if clicked_action == remove_action:
            self._confirm_remove()
        if clicked_action == dev_action:
            print(self.doc.to_dict())

    def _confirm_deletion(self):
        """Pops up a warning box to prevent accidental data loss."""
        
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to permanently delete '{self.title}'?\n\nThis will remove it from the database and delete all associated files. \nhis will not delete the original scans.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            ticket = DatabaseTicket()
            self.delete_requested.emit(self.doc,ticket)

    def _confirm_remove(self):
        """Pops up a warning box to prevent accidental data loss."""
        
        reply = QMessageBox.question(
            self,
            "Confirm Database Removal",
            f"Are you sure you want to remove '{self.title}' from the database?\n\nThis will remove it from the application database but will not delete any document files.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            ticket = DatabaseTicket()
            self.remove_requested.emit(self.doc,ticket)

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

