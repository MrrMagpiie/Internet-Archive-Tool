
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit,
    QFileDialog, QProgressBar,QTableWidget,
    QComboBox,QLabel,QFormLayout,QStackedWidget
)
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from view.components.Page import Page
from view.components.SchemaForm import SchemaForm
from model.data.document import Document
import json
from config import RESOURCES_PATH

class SingleDocumentPage(Page):

    def __init__(self,parent):
        super().__init__(parent)
        self.stack = QStackedWidget()
        self.create_pages()
        self.create_layout()

    def create_layout(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30) 

        self.main_layout.addWidget(self.stack)

    def create_pages(self):
        self.p1 = self.parent.CreateDocumentPage()
        self.p1.doc_ready.connect(self.to_review)
        self.p2 = self.parent.DocumentReviewPage()

        self.stack.addWidget(self.p1)
        self.stack.addWidget(self.p2)
    
    @pyqtSlot(Document)
    def to_review(self,doc):
        self.stack.setCurrentIndex(1)
        self.p2.set_document(doc)
        

# --------------- Signals ---------------

    @pyqtSlot(Document)
    def db_update(self,doc):
        pass

    @pyqtSlot(str)
    def append_log(self, text):
        self.output_text.append(text.strip())

    @pyqtSlot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    @pyqtSlot()
    def task_finished(self):
        self.output_text.append("\nPipeline completed.\n")
        self.progress_bar.setValue(100)
        self.window().showNormal()
        self.window().raise_()