import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit,
    QComboBox, QLabel, QMessageBox,
    QScrollArea
)
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from view.components.Page import Page
from view.components.SchemaForm import SchemaForm, EditableSchemaForm
from model.data.document import Document
from model.data.schema import DocumentSchema
from model.logic.helpers import clear_layout 
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
        
        self._create_layout()

    def _create_layout(self):
        title_layout = QHBoxLayout()
        self.page_title = QLabel("Schema Editor")
        self.page_title.setObjectName("sectionTitle") 
        title_layout.addWidget(self.page_title)
        
        self.metadata_layout = QVBoxLayout()
        doc_type_layout = QVBoxLayout()

        # Add document type select
        self.doc_type_combo = QComboBox()
        self.doc_type_combo.setObjectName("formComboBox")
        doc_type_layout.addWidget(self.doc_type_combo)

        new_btn = QPushButton('New Schema')
        new_btn.setObjectName("infoBtn")
        new_btn.clicked.connect(self.new_schema_page)
        doc_type_layout.addWidget(new_btn)

        copy_btn = QPushButton('Copy Schema')
        copy_btn.setObjectName("infoBtn")
        copy_btn.clicked.connect(lambda: self.new_schema_page(self.current_schema))
        doc_type_layout.addWidget(copy_btn)
        

        self.metadata_layout.addLayout(doc_type_layout)
        
        # Add metadata input table
        self.form = EditableSchemaForm()
        if self.current_schema:
            self.form.new_form(self.current_schema)
        else:
            self.form.new_form()
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.form)
        
        self.form.new_format.connect(self._save_schema)
        self.metadata_layout.addWidget(scroll_area)

        self.save_btn = QPushButton('Save Schema')
        self.save_btn.setObjectName("primaryActionBtn") 
        self.save_btn.clicked.connect(self.form.save)

        # The Delete Button
        self.delete_btn = QPushButton('Delete Schema')
        self.delete_btn.setObjectName("dangerBtn") 
        self.delete_btn.clicked.connect(self._confirm_deletion)

        btn_layout = QHBoxLayout()
        
        self.default_btn = QPushButton('New Default Template')
        self.default_btn.setObjectName("schemaSecondaryBtn") 
        self.default_btn.clicked.connect(self.form.new_default)
        btn_layout.addWidget(self.default_btn)
        
        self.field_btn = QPushButton('New Field')
        self.field_btn.setObjectName("schemaSecondaryBtn")
        self.field_btn.clicked.connect(self.form.new_field)
        btn_layout.addWidget(self.field_btn)

        # Assemble Main Layout Safely (No duplicates)
        self.main_layout.addLayout(title_layout)
        self.main_layout.addSpacing(10)
        self.main_layout.addLayout(self.metadata_layout)
        self.main_layout.addLayout(btn_layout)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.save_btn)
        self.main_layout.addSpacing(10)
        self.main_layout.addWidget(self.delete_btn)

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

    def new_schema_page(self,schema = None):
        schema_name = "New Schema"
        clear_layout(self.metadata_layout)
        
        title_layout = QHBoxLayout()
        self.page_title.setText("Create New Schema")
        
        self.doc_type_line = QLineEdit(schema_name)
        self.doc_type_line.setObjectName("formLineEdit")
        self.metadata_layout.addWidget(self.doc_type_line)
        
        self.form = EditableSchemaForm()
        self.form.new_form(schema)
        self.form.new_format.connect(self._save_schema)
        
        self.field_btn.clicked.connect(self.form.new_field)
        self.default_btn.clicked.connect(self.form.new_default)
        self.save_btn.clicked.connect(self.form.save)
        self.delete_btn.setText("Cancel")
        self.delete_btn.clicked.disconnect()
        self.delete_btn.clicked.connect(self._reset)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.form)
        
        self.metadata_layout.addWidget(scroll_area)

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
        
        if hasattr(self, 'doc_type_line') and self.doc_type_line.isVisible():
            current_schema = self.doc_type_line.text()
            schema_dict['schema_name'] = current_schema
        elif hasattr(self, 'doc_type_combo') and self.doc_type_combo.isVisible():
            current_schema = self.doc_type_combo.currentText()
            schema_dict['schema_name'] = current_schema
        else:
            schema_dict['schema_name'] = "Custom Schema"
            
        schema = DocumentSchema.from_dict(schema_dict)
        self.new_schema.emit(schema)
        self._reset(current_schema)

    def _delete_schema(self):
        if self.current_schema:
            schema_name = self.current_schema.get('schema_name')
            self.delete_schema.emit(schema_name)
            self._reset()

    @pyqtSlot()
    def _reset(self,schema_name=None):
        clear_layout(self.main_layout)
        self._create_layout()
        if schema_name:
            self.doc_type_combo.setCurrentText(schema_name)