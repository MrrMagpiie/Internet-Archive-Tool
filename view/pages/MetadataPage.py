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
from model.service.signals import JobTicket
from model.data.metadata import Metadata
from model.data.document import Document
from model.data.schema import DocumentSchema
from model.logic.helpers import *
import json
from config import DOCUMENT_SCHEMA_PATH

class MetadataPage(Page):
    new_schema = pyqtSignal(DocumentSchema)
    next_stage = pyqtSignal()
    save_metadata = pyqtSignal(object,QObject)

    def __init__(self, parent):
        super().__init__(parent)
        self.form = None
        self.main_layout = QVBoxLayout(self)
        self.create_layout()
        self._load_metadata_formats()
        self.current_document = None

    def create_layout(self):
        title_layout = QHBoxLayout()
        metadata_layout = QVBoxLayout()
        doc_type_layout = QHBoxLayout()

        # add document type select
        self.doc_type_combo = QComboBox()
        doc_type_layout.addWidget(self.doc_type_combo)

        self.doc_type_info = QLabel('Choose a Document Type')
        self.doc_type_info.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        metadata_layout.addWidget(self.doc_type_info)

        self._load_metadata_formats()
        self.doc_type_combo.currentTextChanged.connect(self._on_select_format)
        metadata_layout.addLayout(doc_type_layout)
        
        # add metadata input table
        self.form = SchemaForm()
        metadata_layout.addWidget(self.form)

        # add next stage button
        next_stage_btn = QPushButton('Add Metadata')
        next_stage_btn.clicked.connect(self.to_next_stage)

        self.main_layout.addLayout(title_layout)
        self.main_layout.addLayout(metadata_layout)
        self.main_layout.addStretch()
        self.main_layout.addWidget(next_stage_btn)
        
    # form stuff
    def _load_metadata_formats(self):
        with open(DOCUMENT_SCHEMA_PATH,'r') as f:
            self.metadata_formats = json.load(f)
        self.doc_type_combo.clear()
        for key,value in self.metadata_formats.items():
            self.doc_type_combo.addItem(value['schema_name'], key)

    def _on_select_format(self,format_name=None):
        format_key = self.doc_type_combo.currentData()
        if format_key and format_key != '':
            self.doc_type_info.setVisible(False)
            schema_format = self.metadata_formats[format_key]
            self.form.new_form(schema_format)
        else:
            self.doc_type_info.setVisible(True)
            self.form.clear_form()

    def to_next_stage(self):
        metadata = self.form.get_metadata()
        metadata_type = self.doc_type_combo.currentData()
        data = (self.current_document,metadata,metadata_type)
        
        ticket = JobTicket()
        self.save_metadata.emit(data,ticket)
        self.next_stage.emit()

    def set_current_document(self,document:Document):
        self._reset()
        self.current_document = document
        if document != None:
            cmb_indx = self.doc_type_combo.findText(self.current_document.metadata_file_type)
            self.doc_type_combo.setCurrentIndex(cmb_indx)
            pass

    @pyqtSlot(Document)
    def db_update(self,doc):
        pass

    @pyqtSlot(Document,str)
    def doc_return(self,doc,job_id):
        print('doc ready')

    @pyqtSlot(str,str)
    def doc_error(self,error_msg,job_id):
        pass

    @pyqtSlot(DocumentSchema)
    def _new_schema(self,schema):
        schema_dict = schema.to_dict()
        schema_dict['schema_name'] = self.doc_type_line.text()
        schema = DocumentSchema.from_dict(schema_dict)
        self.new_schema.emit(schema)
        self._reset()

    @pyqtSlot()
    def _reset(self):
        clear_layout(self.main_layout)
        self.create_layout()
        self._on_select_format()
