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
from model.service.signals import JobTicket
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
        image_widget = QWidget()
        image_widget_layout = QVBoxLayout()

        self.deskew_ready_text = QLabel('Document Not Deskewed')
        self.deskew_ready_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
       
        self.image_panel = self.parent.DocumentImagePanel()
        
        image_widget_layout.addWidget(self.deskew_ready_text)
        image_widget_layout.addWidget(self.image_panel)
        
        image_widget.setLayout(image_widget_layout)

        splitter.addWidget(image_widget)
        
        
        # left side
        metadata_widget = QWidget()
        metadata_layout = QVBoxLayout()
        
        self.form = SchemaForm()
        self.meta_ready_text = QLabel('Needs Metadata')
        self.meta_ready_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        
        metadata_layout.addWidget(self.meta_ready_text)
        metadata_layout.addStretch()
        metadata_layout.addWidget(self.form)


        metadata_widget.setLayout(metadata_layout)
        splitter.addWidget(metadata_widget)

        # review and ready text
        

        self.review_layout = QVBoxLayout()
        self.review_layout.setContentsMargins(20, 20, 10, 10)
        self.approve_btn = QPushButton("Approve Document")
        self.reject_btn = QPushButton("Reject Document")
        self.upload_btn = QPushButton("Upload Document")
        self.upload_btn.setVisible(False)

        self.review_layout.addWidget(self.reject_btn)
        self.review_layout.addWidget(self.approve_btn)
        self.review_layout.addWidget(self.upload_btn)
    
        layout.addWidget(splitter)
        
        layout.addLayout(self.review_layout)
        

        self.approve_btn.clicked.connect(self._on_approve)
        self.reject_btn.clicked.connect(self._on_reject)
        self.upload_btn.clicked.connect(self._on_upload)

    def set_current_document(self,doc:Document):
        self.current_document = doc
        if doc != None:
            self.load_metadata()
            if doc.status['deskewed']:
                self.deskew_ready_text.setVisible(False)
                self.image_panel.show_new_document(doc)
            else:
                self.deskew_ready_text.setVisible(True)
        else:
            self.form.clear_form()
            self.image_panel.clear_cache()
            
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

    def _on_upload(self):
        self.upload.emit(self.current_document)

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

            ticket = JobTicket()
            # Emit the entire updated document object to the manager
            self.document_reviewed.emit(self.current_document,ticket)
  
    

