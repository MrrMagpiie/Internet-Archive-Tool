import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout,QGridLayout,
    QPushButton, QLabel, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt,  QObject

from view.components.ActionCard import ActionCard
from model.data.document import Document
from view.components.DocumentImagePanel import DocumentImagePanel 
from view.components.DocumentCard import DocumentCard
from view.components.Page import Page
from model.logic.helpers import clear_layout


class DocumentReviewPage(Page):
    document_reviewed = pyqtSignal(Document,QObject)
    upload = pyqtSignal(Document)
    def __init__(self,parent = None):
        super().__init__(parent)
        self._create_layout()
        self.document = None

    def _create_layout(self):
        """Creates the widget that contains the image viewer and navigation."""
        layout = QVBoxLayout(self)
        
        self.document_card_layout = QHBoxLayout()
        self.image_panel = DocumentImagePanel()

        self.review_layout = QHBoxLayout()
        approve_btn = QPushButton("Approve Document")
        reject_btn = QPushButton("Reject Document")
        self.review_layout.addStretch()
        self.review_layout.addWidget(reject_btn)
        self.review_layout.addWidget(approve_btn)
        self.review_layout.addStretch()

        layout.addLayout(self.document_card_layout)
        layout.addWidget(self.image_panel)
        layout.addLayout(self.review_layout)

        approve_btn.clicked.connect(self._on_approve)
        reject_btn.clicked.connect(self._on_reject)

    def set_document(self,doc:Document):
        self.document = doc
        document_card = DocumentCard(doc)
        clear_layout(self.document_card_layout)
        self.document_card_layout.addWidget(document_card)
        self.image_panel.show_new_document(doc)

    def _approve(self):
        pass

    def _adjust(self):
        pass

    def _on_approve(self):
        self._review_document("approved")
        
    def _on_reject(self):
        self._review_document("rejected")

    def _review_document(self, new_status: str):
        if self.document:
            if new_status == 'approved':
                self.document.status['needs_approval'] = False
                self.document.status['rejected'] = False
                self.document.status['approved'] = True
                upload_btn = QPushButton("Upload Document")
                upload_btn.clicked.connect(lambda:self.upload.emit(self.document))
                self.review_layout.addWidget(upload_btn)

            elif new_status == 'rejected':
                self.document.status['needs_approval'] = False
                self.document.status['rejected'] = True
                self.document.status['approved'] = False

            
            # Emit the entire updated document object to the manager
            self.document_reviewed.emit(self.document,self)
  
    @pyqtSlot(Document)
    def db_update(self,doc):
        if self.document.doc_id == doc.doc_id:
            self.set_document(doc)

