import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout,QGridLayout,
    QPushButton, QLabel, QHBoxLayout, QSplitter
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt,  QObject

from view.components.ActionCard import ActionCard
from view.components.SchemaForm import SchemaForm
from model.data.document import Document
from view.components.DashboardDocumentCard import DocumentCard
from view.components.Page import Page
from model.logic.helpers import clear_layout
from config import ADMIN_UPLOAD


class DocumentReviewPage(Page):
    document_reviewed = pyqtSignal(Document,QObject)
    upload = pyqtSignal(Document)
    next_stage = pyqtSignal()
    
    def __init__(self,parent = None):
        super().__init__(parent)
        self._create_layout()
        self.current_document = None
        self.parent = parent

    def _create_layout(self):
        """Creates the widget that contains the image viewer and navigation."""
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # right side
        self.image_panel = self.parent.DocumentImagePanel()
        splitter.addWidget(self.image_panel)
        
        
        # left side
        self.metadata_panel = QWidget()
        self.metadata_layout = QVBoxLayout()
        
        self.form = SchemaForm()
        self.metadata_layout.addWidget(self.form)

        self.meta_ready_text = QLabel('Needs Metadata')
        self.metadata_layout.addWidget(self.meta_ready_text)

        self.metadata_panel.setLayout(self.metadata_layout)
        splitter.addWidget(self.metadata_panel)

        # review and ready text
        self.deskew_ready_text = QLabel()
        self.deskew_ready_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.deskew_ready_text.setVisible(False)

        self.review_layout = QHBoxLayout()
        approve_btn = QPushButton("Approve Document")
        reject_btn = QPushButton("Reject Document")
        self.review_layout.addStretch()
        self.review_layout.addWidget(reject_btn)
        self.review_layout.addWidget(approve_btn)
        self.review_layout.addStretch()
        

        layout.addWidget(splitter)
        layout.addWidget(self.deskew_ready_text)
        layout.addLayout(self.review_layout)

        approve_btn.clicked.connect(self._on_approve)
        reject_btn.clicked.connect(self._on_reject)

    def set_current_document(self,doc:Document):
        self.current_document = doc
        if doc != None:
            self.load_metadata()
            if doc.status['deskewed']:
                self.deskew_ready_text.setVisible(False)
                self.image_panel.show_new_document(doc)
            else:
                self.deskew_ready_text.setText('Document Not Deskewed')
                self.deskew_ready_text.setVisible(True)
        else:
            self.form.clear_form()
            
    def load_metadata(self):
        '''load metadata for current document'''
        metadata_file = self.current_document.metadata_file
        if metadata_file != None:
            self.meta_ready_text.setVisible(False)
            with open(self.current_document.metadata_file,'r') as f:
                metadata = json.load(f)
                self.form.form_from_metadata(metadata)
        else:
            self.meta_ready_text.setVisible(True)

 # --- Review functions ---
    def _on_approve(self):
        self._review_document("approved")
        
    def _on_reject(self):
        self._review_document("rejected")

    def _review_document(self, new_status: str):
        if self.current_document:
            if new_status == 'approved':
                self.current_document.status['needs_approval'] = True
                self.current_document.status['rejected'] = False
                self.current_document.status['approved'] = True
                upload_btn = QPushButton("Upload Document")
                upload_btn.clicked.connect(lambda:self.upload.emit(self.current_document))
                if not ADMIN_UPLOAD: #or PROFILE == "Admin":
                    self.review_layout.addWidget(upload_btn)

            elif new_status == 'rejected':
                self.current_document.status['needs_approval'] = False
                self.current_document.status['rejected'] = True
                self.current_document.status['approved'] = False

            
            # Emit the entire updated document object to the manager
            self.document_reviewed.emit(self.current_document,self)
  
    

