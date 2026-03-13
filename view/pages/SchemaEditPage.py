import os
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit,
    QFileDialog, QProgressBar, QTableWidget,
    QComboBox, QLabel, QFormLayout, QMessageBox
)
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from view.components.Page import Page
from view.components.SchemaForm import SchemaForm, EditableSchemaForm
from model.service.signals import JobTicket
from model.data.metadata import Metadata
from model.data.document import Document
from model.data.schema import DocumentSchema
from model.logic.helpers import clear_layout # Safely using your external helper
from config import DOCUMENT_SCHEMA_PATH

class SchemaEditPage(Page):
    new_schema = pyqtSignal(DocumentSchema)
    delete_schema = pyqtSignal(str) # schema_name
    next_stage = pyqtSignal()
    save_metadata = pyqtSignal(object, QObject)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.form = None
        self.main_layout = QVBoxLayout(self)
        self.current_schema = None
        
        self.create_layout()

    def create_layout(self):
        title_layout = QHBoxLayout()
        page_title = QLabel("Schema Editor")
        page_title.setObjectName("sectionTitle") # REUSED: Global Typography Hook
        title_layout.addWidget(page_title)
        
        metadata_layout = QVBoxLayout()
        doc_type_layout = QHBoxLayout()

        # Add document type select
        self.doc_type_combo = QComboBox()
        self.doc_type_combo.setObjectName("formComboBox") # REUSED: Form hook
        doc_type_layout.addWidget(self.doc_type_combo)

        new_btn = QPushButton('New Schema')
        new_btn.setObjectName("infoBtn") # REUSED: Global Blue Button
        new_btn.clicked.connect(self.new_schema_page)
        doc_type_layout.addWidget(new_btn)

        metadata_layout.addLayout(doc_type_layout)
        
        # Add metadata input table
        self.form = EditableSchemaForm()
        if self.current_schema:
            self.form.new_form(self.current_schema)
        else:
            self.form.new_form()
            
        self.form.new_format.connect(self._save_schema)
        metadata_layout.addWidget(self.form)

        # The Delete Button
        delete_btn = QPushButton('Delete Schema')
        delete_btn.setObjectName("dangerBtn") # REUSED: Massive inline CSS deleted!
        delete_btn.clicked.connect(self._confirm_deletion)

        # Assemble Main Layout Safely (No duplicates)
        self.main_layout.addLayout(title_layout)
        self.main_layout.addSpacing(10)
        self.main_layout.addLayout(metadata_layout)
        self.main_layout.addStretch()
        self.main_layout.addWidget(delete_btn)

        # Wire up the combo box AFTER the form is instantiated
        self.doc_type_combo.currentTextChanged.connect(self._on_select_schema)
        self._load_metadata_formats()

    # --- Form Stuff ---
    def _load_metadata_formats(self):
        if not Path(DOCUMENT_SCHEMA_PATH).exists():
            return
            
        with open(DOCUMENT_SCHEMA_PATH, 'r') as f:
            self.metadata_formats = json.load(f)
            
        self.doc_type_combo.clear()
        
        for key, value in self.metadata_formats.items():
            self.doc_type_combo.addItem(value['schema_name'], key)

    def _on_select_schema(self, format_name=None):
        format_key = self.doc_type_combo.currentData()
        if format_key and format_key != '':
            schema_format = self.metadata_formats[format_key]
            self.current_schema = schema_format
            self.form.new_form(schema_format)

    def new_schema_page(self):
        schema_name = "New Schema"
        clear_layout(self.main_layout)
        
        title_layout = QHBoxLayout()
        page_title = QLabel("Create New Schema")
        page_title.setObjectName("sectionTitle")
        title_layout.addWidget(page_title)
        
        metadata_layout = QVBoxLayout()

        self.doc_type_line = QLineEdit(schema_name)
        self.doc_type_line.setObjectName("formLineEdit") # NEW: Hook for standard inputs
        metadata_layout.addWidget(self.doc_type_line)
        
        # Add metadata input table
        self.form = EditableSchemaForm()
        self.form.new_form()
        self.form.new_format.connect(self._save_schema)
        metadata_layout.addWidget(self.form)
        
        self.main_layout.addLayout(title_layout)
        self.main_layout.addSpacing(10)
        self.main_layout.addLayout(metadata_layout)
        self.main_layout.addStretch()

    def _confirm_deletion(self):
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion", 
            "Are you sure you want to delete this schema?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            print(f"Executing deletion logic on {self.current_schema}")
            self._delete_schema()
        else:
            print("User canceled the deletion.")

    @pyqtSlot(DocumentSchema)
    def _save_schema(self, schema):
        schema_dict = schema.to_dict()
        
        # FIXED: Check if the widget is actually visible on screen to prevent 
        # overwriting the name with a hidden layout component.
        if hasattr(self, 'doc_type_line') and self.doc_type_line.isVisible():
            schema_dict['schema_name'] = self.doc_type_line.text()
        elif hasattr(self, 'doc_type_combo') and self.doc_type_combo.isVisible():
            schema_dict['schema_name'] = self.doc_type_combo.currentText()
        else:
            schema_dict['schema_name'] = "Custom Schema"
            
        schema = DocumentSchema.from_dict(schema_dict)
        self.new_schema.emit(schema)
        self._reset()

    def _delete_schema(self):
        if self.current_schema:
            schema_name = self.current_schema.get('schema_name')
            self.delete_schema.emit(schema_name)
            self._reset()

    @pyqtSlot()
    def _reset(self):
        clear_layout(self.main_layout)
        self.create_layout()
        # No need to manually call _on_select_schema here, as create_layout 
        # repopulates the combobox which triggers the signal automatically!