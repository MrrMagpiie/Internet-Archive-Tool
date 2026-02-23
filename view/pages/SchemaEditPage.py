import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit,
    QFileDialog, QProgressBar,QTableWidget,
    QComboBox,QLabel,QFormLayout,QMessageBox
)
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from view.components.Page import Page
from view.components.SchemaForm import SchemaForm, EditableSchemaForm
from model.service.signals import JobTicket
from model.data.metadata import Metadata
from model.data.document import Document
from model.data.schema import DocumentSchema
from model.logic.helpers import *
import json
from config import RESOURCES_PATH

class SchemaEditPage(Page):
    new_schema = pyqtSignal(DocumentSchema)
    delete_schema = pyqtSignal(str) # schema_name
    next_stage = pyqtSignal()
    save_metadata = pyqtSignal(object,QObject)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.form = None
        self.main_layout = QVBoxLayout(self)
        self.current_schema = None
        self.create_layout()
        self._load_metadata_formats()
        

    def create_layout(self):
        title_layout = QHBoxLayout()
        metadata_layout = QVBoxLayout()
        doc_type_layout = QHBoxLayout()

        # add document type select
        self.doc_type_combo = QComboBox()
        doc_type_layout.addWidget(self.doc_type_combo)

        new_btn = QPushButton('New')
        new_btn.clicked.connect(lambda:self.new_schema_page())
        doc_type_layout.addWidget(new_btn)

        self._load_metadata_formats()
        self.doc_type_combo.currentTextChanged.connect(self._on_select_schema)
        metadata_layout.addLayout(doc_type_layout)
        
        delete_btn = QPushButton('Delete')
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #d73a49; /* A professional, soft red */
                color: white;              /* White text */
                border-radius: 6px;        /* Rounded corners */
                padding: 8px 16px;         /* Breathing room inside the button */
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cb2431; /* Slightly darker red when hovered */
            }
            QPushButton:pressed {
                background-color: #b31d28; /* Even darker when clicked */
            }
        """)
        delete_btn.clicked.connect(self._confirm_deletion)
        
        
        # add metadata input table
        self.form = EditableSchemaForm()
        self.form.new_form(self.current_schema)
        self.form.new_format.connect(self._save_schema)
        metadata_layout.addWidget(self.form)
        self.main_layout.addLayout(metadata_layout)


        self.main_layout.addLayout(title_layout)
        self.main_layout.addLayout(metadata_layout)
        self.main_layout.addWidget(delete_btn)

    # form stuff
    def _load_metadata_formats(self):
        with open(RESOURCES_PATH /'document_schema.json','r') as f:
            self.metadata_formats = json.load(f)
        self.doc_type_combo.clear()
        for key,value in self.metadata_formats.items():
            self.doc_type_combo.addItem(value['schema_name'], key)

    def _on_select_schema(self,format_name=None):
        format_key = self.doc_type_combo.currentData()
        if format_key and format_key != '':
            schema_format = self.metadata_formats[format_key]
            self.current_schema = schema_format
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


    def new_schema_page(self):
        schema_name = "New"
        clear_layout(self.main_layout)
        # add document type select
        metadata_layout = QVBoxLayout()

        self.doc_type_line = QLineEdit(schema_name)
        metadata_layout.addWidget(self.doc_type_line)
        
        # add metadata input table
        self.form = EditableSchemaForm()
        self.form.new_form()
        self.form.new_format.connect(self._save_schema)
        metadata_layout.addWidget(self.form)
        self.main_layout.addLayout(metadata_layout)

    def _confirm_deletion(self):
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion", 
            "Are you _confirm_deletion you want to delete this schema?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            print(f"Executing deletion logic on {self.current_schema}")
            self._delete_schema()
        else:
            print("User canceled the deletion.")

    @pyqtSlot(DocumentSchema)
    def _save_schema(self,schema):
        schema_dict = schema.to_dict()
        schema_dict['schema_name'] = self.doc_type_line.text()
        schema = DocumentSchema.from_dict(schema_dict)
        self.new_schema.emit(schema)
        self._reset()

    def _delete_schema(self):
        schema_name = self.current_schema.get('schema_name')
        self.delete_schema.emit(schema_name)
        self._reset()

    @pyqtSlot()
    def _reset(self):
        clear_layout(self.main_layout)
        self.create_layout()
        self._on_select_schema()
