import os
from PyQt6.QtWidgets import (
    QWidget, QTextEdit, QLineEdit,
    QTableWidget,QComboBox,QLabel,
    QFormLayout, QFrame, QPushButton,
    QHBoxLayout,QVBoxLayout
)
from config import RESOURCES_PATH
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from model.data.schema import DocumentSchema
from model.data.metadata import Metadata
from model.logic.helpers import clear_layout
import json



class SchemaForm(QWidget):
    def __init__(self):
        super().__init__()
        self._create_layout()
        self.current_schema: DocumentSchema = None

    def _create_layout(self):
        self.form_layout = QFormLayout(self)

    def _build_form(self):
        fields = self.current_schema.to_dict().get('fields')
        self.clear_form
        if isinstance(fields,dict):
            for key,value in fields.items():
                    label = QLabel(key)
                    self.form_layout.addRow(label, QLineEdit())
    
    @pyqtSlot(dict)
    def new_form(self,schema_format:dict):
        self.current_schema = DocumentSchema.from_dict(schema_format)
        self._build_form()

    def form_from_metadata(self,metadata):
        self.clear_form()
        for key,value in metadata.items():
                self.form_layout.addRow(QLabel(key), QLabel(value))

    def clear_form(self):
        clear_layout(self.form_layout)


    def _write_form_to_schema(self) -> Dict[str, Any]:
        """Helper: Scrapes the UI to get the current field values."""
        updated_fields = {}
        for row in range(self.form_layout.rowCount()):
            label_item = self.form_layout.itemAt(row, QFormLayout.ItemRole.LabelRole)
            field_item = self.form_layout.itemAt(row, QFormLayout.ItemRole.FieldRole)
            
            if label_item and field_item:
                key = label_item.widget().text()
                value = field_item.widget().text()
                self.current_schema.edit_field(key,value)

    def get_metadata(self) -> Metadata:
        self._write_form_to_schema()
        metadata = self.current_schema.generate_metadata()
        return metadata
    
    def get_schema_format(self) -> dict:
        self._write_form_to_schema()
        schema_dict = self.current_schema.to_dict()
        return dict


class EditableSchemaForm(SchemaForm):
    new_format = pyqtSignal(DocumentSchema)
    cancel = pyqtSignal()
    error_window = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.schema_dict = None
        self._load_ia_keys()
        self._load_default_format()       

    def _create_layout(self):
        self.form_layout = QFormLayout() 
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self.form_layout)
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)

        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(self._cancel)
        
        default_btn = QPushButton('New Default')
        default_btn.clicked.connect(self.new_default)
        btn_layout.addWidget(default_btn)
        
        field_btn = QPushButton('New Field')
        field_btn.clicked.connect(self.new_field)
        btn_layout.addWidget(field_btn)

        
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(save_btn)
        main_layout.addWidget(cancel_btn)

    def _load_ia_keys(self):
        with open(RESOURCES_PATH /'IAMetadataKeys.json','r') as f:
            self.IA_keys = json.load(f)

    def _load_default_format(self):
        with open(RESOURCES_PATH /'default_schema.json','r') as f:
            self.default_format = json.load(f)

    def new_form(self,schema_format:dict = None):
        if schema_format == None:
            self.schema_dict = self.default_format['default']
        else:
            self.schema_dict = schema_format
        self._update_form()

    def _update_form(self):
        self._build_form()

    def _default_row(self,key = '',value =''):
        key_combo = QComboBox()
        key_combo.setEditable(True) 
        
        if isinstance(self.IA_keys, dict):
            key_combo.addItems(list(self.IA_keys.keys()))
        value_input = QLineEdit(value)
        value_input.setProperty('type','default_value')
        key_combo.setCurrentText(key)
        key_combo.setProperty('type','default_key')
        
        self.form_layout.addRow(key_combo, value_input)

    def add_section_header(self, title_text):
        """Adds a bold label and a horizontal line to simulate a section."""
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        
        header_label = QLabel(title_text)
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")

        self.form_layout.addRow(header_label)
        self.form_layout.addRow(line)

    def new_default(self):
        self._write_form_to_schema()
        try:
            blanks = int(self.schema_dict['defaults']['blank'])
            blanks +=1
            self.schema_dict['defaults']['blank'] = str(blanks)
        except:
            self.schema_dict['defaults']['blank'] = "1"
        self._update_form()

    def new_field(self):
        self._write_form_to_schema()
        try:
            blanks = int(self.schema_dict['fields']['blank']) 
            blanks +=1
            self.schema_dict['fields']['blank'] = str(blanks)
        except:
            self.schema_dict['fields']['blank'] = "1"
        self._update_form()

    def _build_form(self):
        fields = self.schema_dict.get('fields')
        defaults = self.schema_dict.get('defaults')

        self.clear_form()
        self.add_section_header('fields')
        if isinstance(fields,dict):
            for key,value in fields.items():
                if key == 'blank':
                    for x in range(int(value)):
                        line = QLineEdit()
                        line.setProperty('type','field')
                        self.form_layout.addRow(line)
                else:
                    label = QLineEdit(key)
                    label.setProperty('type','field')
                    self.form_layout.addRow(label)
                
        self.add_section_header('defaults')
        if isinstance(defaults,dict):
            for key,value in defaults.items():
                if key == 'blank':
                    for x in range(int(value)):
                        self._default_row()
                else:
                    self._default_row(key,value)
                
    def _save(self):
        self._write_form_to_schema()
        try:
            schema = DocumentSchema.from_dict(self.schema_dict)
        except Exception as e:
            self.error_window.emit(str(e))
            return
        self.new_format.emit(schema)

    def _cancel(self):
        self.cancel.emit()

    def _write_form_to_schema(self):
        new_fields = {}
        new_defaults = {}

        for row in range(self.form_layout.rowCount()):
            
            label_item = self.form_layout.itemAt(row, QFormLayout.ItemRole.LabelRole)
            field_item = self.form_layout.itemAt(row, QFormLayout.ItemRole.FieldRole)
            spanning_item = self.form_layout.itemAt(row, QFormLayout.ItemRole.SpanningRole)

            if label_item and field_item:
                key_widget = label_item.widget()
                val_widget = field_item.widget()
                
                if key_widget and key_widget.property('type') == 'default_key':
                    key = key_widget.currentText()
                    val = val_widget.text()
                    if key:
                        new_defaults[key] = val

            elif spanning_item:
                widget = spanning_item.widget()
                
                if widget and widget.property('type') == 'field':
                    text = widget.text()
                    if text:
                        new_fields[text] = ""

        self.schema_dict['fields'] = new_fields
        self.schema_dict['defaults'] = new_defaults