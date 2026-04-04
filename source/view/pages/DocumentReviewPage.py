import sys
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout,
    QPushButton, QLabel, QHBoxLayout,
    QDialog, QFrame
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt,  QObject
from PyQt6.QtGui import QFont

from view.components.SchemaForm import SchemaForm
from model.data.document import Document
from view.components.DashboardCards import DocumentCard
from view.components.Page import Page
from model.logic.helpers import clear_layout
from model.logic.upload import IdentifierStatus
from model.service.Signals import JobTicket, DatabaseTicket
from model.settings_manager import app_settings


class DocumentReviewPage(Page):
    document_reviewed = pyqtSignal(Document, QObject)
    upload = pyqtSignal(Document, object)
    unique_identifier = pyqtSignal(str, object)
    identifier_status = pyqtSignal(str, object)
    save_metadata = pyqtSignal(tuple, QObject)
    next_stage = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_document = None
        self.parent = parent
        self.pending_requests = {}
        self._create_layout()

    def _create_layout(self):
        """Creates the widget that contains the image viewer and navigation."""
        main_layout = QVBoxLayout(self)
        panel_layout = QHBoxLayout()

        # left side
        image_widget = QWidget()
        image_widget_layout = QVBoxLayout()

        self.deskew_ready_text = QLabel('Document Not Deskewed')
        self.deskew_ready_text.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.deskew_ready_text.setObjectName("warningText") 
       
        self.image_panel = self.parent.create_document_image_panel()
        
        image_widget_layout.addWidget(self.deskew_ready_text)
        image_widget_layout.addWidget(self.image_panel)
        
        image_widget.setLayout(image_widget_layout)
        panel_layout.addWidget(image_widget)
        
        # Minimal separator bar
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        panel_layout.addWidget(separator)
        
        
        # right side
        metadata_widget = QWidget()
        metadata_layout = QVBoxLayout()
        
        self.form = SchemaForm()
        self.meta_ready_text = QLabel('Needs Metadata')
        self.meta_ready_text.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.meta_ready_text.setObjectName("warningText") 
        
        metadata_layout.addWidget(self.meta_ready_text)
        metadata_layout.addWidget(self.form)

        metadata_widget.setLayout(metadata_layout)
        panel_layout.addWidget(metadata_widget)

        # review and ready text
        self.review_layout = QVBoxLayout()
        self.review_layout.setContentsMargins(50, 50, 10, 10)
        
        self.approve_btn = QPushButton("Approve Document")
        self.approve_btn.setObjectName("successBtn") 
        
        self.reject_btn = QPushButton("Reject Document")
        self.reject_btn.setObjectName("dangerBtn") 
        
        self.upload_btn = QPushButton("Upload Document")
        self.upload_btn.setObjectName("primaryActionBtn")
        self.upload_btn.setVisible(False)

        self.review_layout.addWidget(self.reject_btn)
        self.review_layout.addWidget(self.approve_btn)
        self.review_layout.addWidget(self.upload_btn)
    
        main_layout.addLayout(panel_layout)
        main_layout.addLayout(self.review_layout)
        
        self.approve_btn.clicked.connect(self._on_approve)
        self.reject_btn.clicked.connect(self._on_reject)
        self.upload_btn.clicked.connect(self._on_upload)

    def set_current_document(self, doc: Document):
        self.current_document = doc
        if doc != None:
            self.check_metadata()
            if doc.status['deskewed']:
                self.deskew_ready_text.setVisible(False)
                self.image_panel.show_new_document(doc)
            else:
                self.deskew_ready_text.setVisible(True)
        else:
            self.form.clear_form()
            self.image_panel.clear_cache()
            
    def check_metadata(self):
        '''load metadata for current document'''
        if self.current_document.metadata != None:
            self.meta_ready_text.setVisible(False)
            self.update_metadata_form()
        else:
            self.meta_ready_text.setVisible(True)

    def update_metadata_form(self):
        metadata = self.current_document.metadata.to_dict()
        self.form.list_from_metadata(metadata)

    # --- Review functions ---
    def _on_approve(self):
        self._review_document("approved")
        
    def _on_reject(self):
        self._review_document("rejected")

    def _on_upload(self):
        if app_settings.get('AUTO_GENERATE_IDENTIFIER'):
            self.request_unique_identifier()
        else:
            self.request_identifier_status()

    def _review_document(self, new_status: str):
        if self.current_document:
            if new_status == 'approved':
                self.current_document.status['needs_approval'] = True
                self.current_document.status['rejected'] = False
                self.current_document.status['approved'] = True
                if not app_settings.get('ADMIN_UPLOAD'): 
                    self.upload_btn.setVisible(True)
                    
            elif new_status == 'rejected':
                self.current_document.status['needs_approval'] = False
                self.current_document.status['rejected'] = True
                self.current_document.status['approved'] = False

            ticket = DatabaseTicket()
            self.document_reviewed.emit(self.current_document, ticket)
            self.next_stage.emit()
        
    # --- Requests & Returns ---
    def request_identifier_status(self):
        ticket = JobTicket()
        ticket.data.connect(self._handle_status_return)
        identifier = self.current_document.metadata.identifier
        self.identifier_status.emit(identifier, ticket)

    @pyqtSlot(object, str)
    def _handle_status_return(self, status: IdentifierStatus, job_id):
        if app_settings.get('AUTO_GENERATE_IDENTIFIER'):
            match status:
                case IdentifierStatus.FREE:
                    self.request_upload()
                case IdentifierStatus.ACTIVE | IdentifierStatus.OFFLINE:
                    self.request_unique_identifier()
        else:
            match status:
                case IdentifierStatus.FREE:
                    self.request_upload()
                case IdentifierStatus.ACTIVE| IdentifierStatus.OFFLINE:
                    self.collision_dialog_popup(status)
                    
    def collision_dialog_popup(self, status):
        self.collision_modal = CollisionResolutionDialog(self.current_document.metadata.identifier, status, self)
        self.collision_modal.user_choice.connect(self._handle_user_collision_choice)

    @pyqtSlot(str)
    def _handle_user_collision_choice(self, identifier):
        self.current_document.metadata.identifier = identifier
        ticket = JobTicket()
        ticket.data.connect(self._handle_save_metadata)
        data = (self.current_document, self.current_document.metadata, self.current_document.metadata_file_type)
        self.save_metadata.emit(data, ticket)

    @pyqtSlot(object, str)
    def _handle_save_metadata(self, doc, job_id):
        self.request_upload()

    def request_upload(self):
        ticket = JobTicket()
        ticket.data.connect(self._handle_upload_success)
        ticket.error.connect(self._handle_upload_error)
        self.upload.emit(self.current_document, ticket)
        self.next_stage.emit()

    @pyqtSlot(object, str)
    def _handle_upload_success(self, doc, job_id):
        print('upload_success')

    @pyqtSlot(Exception, str)
    def _handle_upload_error(self, error, job_id):
        print(f'upload_error:{error}')

class CollisionResolutionDialog(QDialog):
    user_choice = pyqtSignal(str)
    
    def __init__(self, identifier: str, status: IdentifierStatus, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Identifier Collision Detected")
        self.setModal(True)
        self.status = status
        self.original_identifier = identifier
        self.request_unique_identifier()
        
    def _create_layout(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # --- 1. The Warning Message ---
        lbl_title = QLabel("Identifier Already Exists")
        lbl_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        
        status_color = "#d73a49" if self.status == IdentifierStatus.OFFLINE else "#28a745"
        status_text = "Unavailable" if self.status == IdentifierStatus.OFFLINE else "Active"
        continue_color = "#0366d6"
        new_color = "#28a745"
        cancel_color = "#d73a49"
        
        # Qt Rich Text naturally handles HTML colors perfectly, so leaving this inline is preferred!
        lbl_info = QLabel(
            f"The identifier <b>{self.original_identifier}</b> is currently <b style='color: {status_color};'>{status_text}</b> on the Internet Archive.<br><br>"
            f"• <b style='color: {continue_color};'>Continue</b> with current identifier to upload to the existing document<br>"
            f"• Use the suggested identifier to create a <b style='color: {new_color};'>New</b> document<br>"
            f"• Or <b style='color: {cancel_color};'>Cancel</b> the upload"
        )
        
        # --- 2. The Suggested Solution Box ---
        suggestion_frame = QFrame()
        suggestion_frame.setObjectName("suggestionFrame") 
        frame_layout = QVBoxLayout(suggestion_frame)
        
        lbl_suggestion = QLabel(f"<b>Suggested New Identifier:</b><br><span style='font-family: monospace; font-size: 14px;'>{self.unique_identifier}</span>")
        frame_layout.addWidget(lbl_suggestion)

        # --- 3. The Interactive Buttons ---
        btn_layout = QHBoxLayout()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("dangerBtn") 
        btn_cancel.clicked.connect(self.choose_cancel)
        
        btn_update = QPushButton("Continue")
        btn_update.setObjectName("infoBtn") 
        btn_update.clicked.connect(self.choose_update)
        
        btn_accept_new = QPushButton("New")
        btn_accept_new.setObjectName("successBtn") 
        btn_accept_new.clicked.connect(self.choose_new)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addStretch()
        if self.status != IdentifierStatus.OFFLINE:
            btn_layout.addWidget(btn_update)
        btn_layout.addWidget(btn_accept_new)
        
        layout.addWidget(lbl_title)
        layout.addWidget(lbl_info)
        layout.addWidget(suggestion_frame)
        layout.addStretch()
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def choose_update(self):
        self.user_choice.emit(self.original_identifier)
        self.accept()

    def choose_new(self):
        self.user_choice.emit(self.unique_identifier)
        self.accept()

    def choose_cancel(self):
        self.reject()

    def request_unique_identifier(self):
        ticket = JobTicket()
        ticket.data.connect(self._handle_unique_identifier)
        self.parent.unique_identifier.emit(self.parent.current_document.metadata.identifier, ticket)
    
    @pyqtSlot(object, str)
    def _handle_unique_identifier(self, unique_identifier: str, job_id):
        self.unique_identifier = unique_identifier
        self._create_layout()
        self.show()