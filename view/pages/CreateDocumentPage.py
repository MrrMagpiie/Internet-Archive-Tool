
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit,
    QFileDialog, QProgressBar,QTableWidget,
    QComboBox,QLabel,QFormLayout
)
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from view.components.Page import Page
from view.components.SchemaForm import SchemaForm, EditableSchemaForm
from model.data.metadata import Metadata
from model.data.document import Document
from model.data.schema import DocumentSchema
from model.logic.helpers import *
import json
from config import RESOURCES_PATH

class CreateDocumentPage(Page):
    doc_ready = pyqtSignal(Document)
    start_document_process = pyqtSignal(tuple,QObject)
    new_schema = pyqtSignal(DocumentSchema)

    def __init__(self,parent):
        super().__init__(parent)
        self.form = None
        self.main_layout = QVBoxLayout(self)
        self.create_layout()
        self._load_metadata_formats()

    def create_layout(self):
        input_layout = QHBoxLayout()
        self.input_dir_field = QLineEdit()
        input_layout.addWidget(self.input_dir_field)
        input_browse_btn = QPushButton("Select Document Folder")
        input_browse_btn.clicked.connect(lambda: self.select_directory(self.input_dir_field))
        input_layout.addWidget(input_browse_btn)
        self.main_layout.addLayout(input_layout)

        # add document type select
        metadata_layout = QVBoxLayout()
        doc_type_layout = QHBoxLayout()
        
        self.doc_type_combo = QComboBox()
        doc_type_layout.addWidget(self.doc_type_combo)

        edit_btn = QPushButton('Edit')
        edit_btn.clicked.connect(lambda:self.edit_page(self.metadata_formats[self.doc_type_combo.currentData()]))
        doc_type_layout.addWidget(edit_btn)

        new_btn = QPushButton('New')
        new_btn.clicked.connect(lambda:self.edit_page())
        doc_type_layout.addWidget(new_btn)

        self._load_metadata_formats()
        self.doc_type_combo.currentTextChanged.connect(self._on_select_format)
        metadata_layout.addLayout(doc_type_layout)
        
        # add metadata input table
        self.form = SchemaForm()
        metadata_layout.addWidget(self.form)
        self.main_layout.addLayout(metadata_layout)
        
        run_btn = QPushButton("Start Process")
        run_btn.clicked.connect(self.processButtonCallback)


        self.main_layout.addWidget(run_btn)


    # Discovery stuff
    def select_directory(self, field):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            field.setText(dir_path)

    def get_paths(self):
        input_dir = self.input_dir_field.text().strip()
        output_dir = input_dir + '/deskewed'

        if not input_dir or not os.path.isdir(input_dir):
            return None, None
        print(input_dir,output_dir)
        return input_dir, output_dir

    def processButtonCallback(self):
        input_dir, out_dir = self.get_paths()
        metadata = self.form.get_metadata()
        metadata_type = self.doc_type_combo.currentData()

        data = (input_dir,out_dir,metadata,metadata_type)
        self.start_document_process.emit(data,self)

    # form stuff
    def _load_metadata_formats(self):
        with open(RESOURCES_PATH /'document_schema.json','r') as f:
            self.metadata_formats = json.load(f)
        self.doc_type_combo.clear()
        for key,value in self.metadata_formats.items():
            self.doc_type_combo.addItem(value['schema_name'], key)

    def _on_select_format(self,format_name=None):
        format_key = self.doc_type_combo.currentData()
        if format_key and format_key != '':
            schema_format = self.metadata_formats[format_key]
            self.form.new_form(schema_format)

    def clear_layout(self, layout):
        """Removes all widgets from a layout and schedules them for deletion."""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    @pyqtSlot(Document)
    def db_update(self,doc):
        pass

    @pyqtSlot(Document)
    def doc_return(self,doc):
        self.doc_ready.emit(doc)

    @pyqtSlot(str)
    def doc_error(self,error_msg):
        pass

    def edit_page(self,schema=None):
        if schema:
            schema_name = schema['schema_name']
        else:
            schema_name = "New"
        clear_layout(self.main_layout)
        # add document type select
        metadata_layout = QVBoxLayout()

        self.doc_type_line = QLineEdit(schema_name)
        metadata_layout.addWidget(self.doc_type_line)
        

        # add metadata input table
        self.form = EditableSchemaForm()
        self.form.new_form(schema)
        self.form.new_format.connect(self._new_schema)
        self.form.cancel.connect(self._reset)
        metadata_layout.addWidget(self.form)
        self.main_layout.addLayout(metadata_layout)

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