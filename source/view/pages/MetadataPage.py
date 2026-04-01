import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit,
    QFileDialog, QProgressBar,QTableWidget,
    QComboBox,QLabel,QFormLayout
)
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, Qt
from view.components.Page import Page
from view.components.SchemaForm import SchemaForm, EditableSchemaForm
from model.service.signals import JobTicket, DatabaseTicket
from model.data import Metadata,Document,DocumentSchema
from model.logic import *
from model.logic.helpers import clear_layout, load_metadata_formats
import json
from config import DOCUMENT_SCHEMA_PATH

class MetadataPage(Page):
    new_schema = pyqtSignal(DocumentSchema)
    next_stage = pyqtSignal()
    save_metadata = pyqtSignal(Document,DatabaseTicket)

    def __init__(self, parent):
        super().__init__(parent)
        self.current_document = None
        self.form = None
        self.metadata_formats = load_metadata_formats()
        self.main_layout = QVBoxLayout(self)
        self._create_layout()
        
    def _create_layout(self):
        title_layout = QHBoxLayout()
        metadata_layout = QVBoxLayout()
        doc_type_layout = QHBoxLayout()

        # add document type select
        self.doc_type_combo = QComboBox()
        doc_type_layout.addWidget(self.doc_type_combo)

        self.doc_type_info = QLabel('Choose a Document Type')
        self.doc_type_info.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        metadata_layout.addWidget(self.doc_type_info)

        self._populate_metadata_formats()
        self.doc_type_combo.currentTextChanged.connect(self._on_select_format)
        metadata_layout.addLayout(doc_type_layout)
        
        # add metadata input table
        self.form = SchemaForm()
        self.current_metadata_form = SchemaForm()
        self.current_metadata_form.setVisible(False)
        metadata_layout.addWidget(self.form)
        metadata_layout.addWidget(self.current_metadata_form)

        # add next stage button
        next_stage_btn = QPushButton('Add Metadata')
        next_stage_btn.setObjectName("primaryActionBtn")
        next_stage_btn.clicked.connect(self.to_next_stage)

        self.main_layout.addLayout(title_layout)
        self.main_layout.addLayout(metadata_layout)
        self.main_layout.addStretch()
        self.main_layout.addWidget(next_stage_btn)

    def _populate_metadata_formats(self):
        self.doc_type_combo.clear()
        self.doc_type_combo.addItem('', '')
        for key,value in load_metadata_formats().items():
            self.doc_type_combo.addItem(value['schema_name'], key)

    def _on_select_format(self):
        format_key = self.doc_type_combo.currentData()
        print(format_key)
        if format_key and format_key != '':
            self.doc_type_info.setVisible(False)
            self.create_form(format_key)
        else:
            self.doc_type_info.setVisible(True)
            self.form.clear_form()

        if self.current_document and self.current_document.metadata:
            self.current_metadata_form.list_from_metadata(self.current_document.metadata.to_dict())
            self.current_metadata_form.setVisible(True)
        else:
            self.current_metadata_form.setVisible(False)

    def create_form(self,format_key):
        if self.current_document and self.current_document.metadata_file_type == format_key:
            metadata = self.current_document.metadata.to_dict()
            schema_format = self.metadata_formats[format_key]
            self.form.from_metadata(schema_format,metadata)
        else:
            schema_format = self.metadata_formats[format_key]
            self.form.new_form(schema_format)

    def to_next_stage(self):
        metadata = self.form.get_metadata()
        metadata_type = self.doc_type_combo.currentData()
        self.current_document.metadata_file_type = metadata_type
        self.current_document.add_metadata(metadata)
        
        ticket = DatabaseTicket()
        self.save_metadata.emit(self.current_document,ticket)
        self.next_stage.emit()

    def set_current_document(self,document:Document):
        self._reset()
        self.current_document = document
        if document != None:
            cmb_indx = self.doc_type_combo.findText(self.current_document.metadata_file_type)
            self.doc_type_combo.setCurrentIndex(cmb_indx)

    @pyqtSlot(Document)
    def document_update(self,doc):
        pass

    @pyqtSlot(Document,str)
    def doc_return(self,doc,job_id):
        print('doc ready')

    @pyqtSlot(str,str)
    def doc_error(self,error_msg,job_id):
        pass

    @pyqtSlot()
    def _reset(self):
        clear_layout(self.main_layout)
        self._create_layout()
