
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit,
    QFileDialog, QProgressBar,QTableWidget,
    QComboBox,QLabel,QFormLayout
)
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from view.components.Page import Page
from view.components.SchemaForm import SchemaForm
from model.data.metadata import Metadata
from model.data.document import Document
import json
from config import RESOURCES_PATH

class SchemaBuilderPage(Page):

    def __init__(self,parent):
        super().__init__(parent)
        self.form = None
        self.create_layout()
        self._load_metadata_formats()

    def create_layout(self):
        main_layout = QVBoxLayout(self)
        
        # add document type select
        metadata_layout = QVBoxLayout()
        self.doc_type_combo = QComboBox()
        self._load_metadata_formats()
        self.doc_type_combo.currentTextChanged.connect(self._on_select_format)
        metadata_layout.addWidget(self.doc_type_combo)
        
        # add metadata input table
        self.form = SchemaForm()
        metadata_layout.addWidget(self.form)
        main_layout.addLayout(metadata_layout)
        
        
        save_btn = QPushButton("Save Format")
        save_btn.clicked.connect(self.saveButtonCallback)
        main_layout.addWidget(save_btn)

    def saveButtonCallback(self):
        pass

    # form stuff
    def _load_metadata_formats(self):
        with open(RESOURCES_PATH /'document_schema.json','r') as f:
            self.metadata_formats = json.load(f)
        self.doc_type_combo.clear()
        for key,value in self.metadata_formats.items():
            self.doc_type_combo.addItem(value['schema_name'], key)

    def _on_select_format(self,format_name):
        format_key = self.doc_type_combo.currentData()
        if format_key and format_key != '':
            schema_format = self.metadata_formats[format_key]
            self.form.new_form(schema_format)

    @pyqtSlot(Document)
    def db_update(self,doc):
        pass

    @pyqtSlot(Document)
    def doc_return(self,doc):
        self.doc_ready.emit(doc)

    @pyqtSlot(str)
    def doc_error(self,error_msg):
        pass
