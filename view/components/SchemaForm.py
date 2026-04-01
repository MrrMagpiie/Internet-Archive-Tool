import os
import json
from PyQt6.QtWidgets import (
    QWidget, QTextEdit, QLineEdit,
    QTableWidget, QComboBox, QLabel,
    QFormLayout, QFrame, QPushButton,
    QHBoxLayout, QVBoxLayout
)
from PyQt6.QtGui import QIntValidator, QDoubleValidator, QRegularExpressionValidator
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QRegularExpression

from config import FIELD_TYPES_PATH, RESOURCES_PATH
from model.data.schema import DocumentSchema
from model.data.metadata import Metadata
from model.logic.helpers import clear_layout


class SchemaForm(QWidget):
    def __init__(self):
        super().__init__()
        self._create_layout()
        self.current_schema: DocumentSchema = None
        
        self._load_field_rules()

    def _load_field_rules(self):
        if FIELD_TYPES_PATH.exists():
            with open(FIELD_TYPES_PATH, 'r') as f:
                self.field_rules = json.load(f)
        else:
            self.field_rules = {}

    def _create_layout(self):
        self.form_layout = QFormLayout(self)

    def _build_form(self):
        fields = self.current_schema.to_dict().get('fields')
        self.clear_form()
        
        if isinstance(fields, dict):
            for field_name, field_type_name in fields.items():
                label = QLabel(field_name)
                input_widget = QLineEdit()
                
                # Apply dynamic UI validation based on the schema's specified type
                self._apply_validation_rules(input_widget, field_type_name)
                
                self.form_layout.addRow(label, input_widget)

    def _build_form_from_metadata(self, metadata: dict):
        fields = self.current_schema.to_dict().get('fields')
        self.clear_form()
        
        if isinstance(fields, dict):
            for field_name, field_type_name in fields.items():
                label = QLabel(field_name)
                input_widget = QLineEdit()
                input_widget.setText(str(metadata.get(field_name, '')))
                
                # Apply dynamic UI validation based on the schema's specified type
                self._apply_validation_rules(input_widget, field_type_name)
                
                self.form_layout.addRow(label, input_widget)

    def _apply_validation_rules(self, widget: QLineEdit, type_name: str):
        """Looks up the rule in JSON and attaches the correct PyQt6 validator."""
        rule = self.field_rules.get(type_name, {"type": "string"})
        
        if "placeholder" in rule:
            widget.setPlaceholderText(rule["placeholder"])
            
        validation_type = rule.get("type")
        
        if validation_type == "integer":
            widget.setValidator(QIntValidator())
        elif validation_type == "float":
            widget.setValidator(QDoubleValidator())
        elif validation_type == "regex":
            pattern = rule.get("pattern", ".*")
            regex = QRegularExpression(pattern)
            widget.setValidator(QRegularExpressionValidator(regex))
    
    @pyqtSlot(dict)
    def new_form(self, schema_format: dict):
        self.clear_form()
        self.current_schema = DocumentSchema.from_dict(schema_format)
        self._build_form()

    def from_metadata(self, schema_format,metadata: dict):
        self.clear_form()
        self.current_schema = DocumentSchema.from_dict(schema_format)
        self._build_form_from_metadata(metadata)

    def list_from_metadata(self,metadata:dict):
        self.clear_form()
        for key, value in metadata.items():
            self.form_layout.addRow(QLabel(key), QLabel(str(value)))

    def clear_form(self):
        clear_layout(self.form_layout)

    def get_user_inputs(self) -> dict:
        """Scrapes the UI to get the user's entered values."""
        inputs = {}
        for row in range(self.form_layout.rowCount()):
            label_item = self.form_layout.itemAt(row, QFormLayout.ItemRole.LabelRole)
            field_item = self.form_layout.itemAt(row, QFormLayout.ItemRole.FieldRole)
            
            if label_item and field_item:
                key = label_item.widget().text()
                value = field_item.widget().text()
                inputs[key] = value
        return inputs

    def get_metadata(self) -> Metadata:
        """Passes the scraped UI inputs to the backend schema generator."""
        user_inputs = self.get_user_inputs()
        metadata = self.current_schema.generate_metadata(user_inputs)
        return metadata
        


class EditableSchemaForm(SchemaForm):
    new_format = pyqtSignal(DocumentSchema)
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

    def _load_ia_keys(self):
        keys_path = RESOURCES_PATH / 'IAMetadataKeys.json'
        if keys_path.exists():
            with open(keys_path, 'r') as f:
                self.IA_keys = json.load(f)
        else:
            self.IA_keys = {}

    def _load_default_format(self):
        fmt_path = RESOURCES_PATH / 'default_schema.json'
        if fmt_path.exists():
            with open(fmt_path, 'r') as f:
                self.default_format = json.load(f)
        else:
            self.default_format = {"default": {"fields": {}, "defaults": {}}}

    def new_form(self, schema_format: dict = None):
        if schema_format:
            self.schema_dict = schema_format
        else:
            self.schema_dict = self.default_format['default']
        self._build_form()

    def add_section_header(self, title_text):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setObjectName("schemaSectionLine") 
        
        header_label = QLabel(title_text)
        header_label.setObjectName("schemaSectionHeader")

        self.form_layout.addRow(header_label)
        self.form_layout.addRow(line)

    # --- Row Builders ---
    def _field_row(self, key_name='', field_type='Text'):
        """Creates a row with a field name and a data type dropdown."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        name_input = QLineEdit(key_name)
        name_input.setPlaceholderText("Field Name (e.g., year)")
        name_input.setProperty('role', 'field_name')
        
        type_combo = QComboBox()
        type_combo.addItems(list(self.field_rules.keys())) 
        type_combo.setCurrentText(field_type if field_type in self.field_rules else 'Text')
        type_combo.setProperty('role', 'field_type')
        
        layout.addWidget(name_input)
        layout.addWidget(type_combo)
        
        self.form_layout.addRow(container)

    def _default_row(self, key='', value=''):
        """Creates a row for Internet Archive default templates."""
        key_combo = QComboBox()
        key_combo.setEditable(True) 
        
        if isinstance(self.IA_keys, dict):
            key_combo.addItems(list(self.IA_keys.keys()))
            
        value_input = QLineEdit(value)
        value_input.setPlaceholderText("e.g., Document_{year}")
        
        key_combo.setCurrentText(key)
        key_combo.setProperty('role', 'default_key')
        
        self.form_layout.addRow(key_combo, value_input)

    # --- Add New Rows ---

    def new_field(self):
        self._write_form_to_schema()
        fields = self.schema_dict.setdefault('fields', {})
        blanks = int(fields.get('blank', 0)) + 1
        fields['blank'] = str(blanks)
        self._build_form()

    def new_default(self):
        self._write_form_to_schema()
        defaults = self.schema_dict.setdefault('defaults', {})
        blanks = int(defaults.get('blank', 0)) + 1
        defaults['blank'] = str(blanks)
        self._build_form()

    def _build_form(self):
        filename_template = self.schema_dict.get('filename_template', '')
        fields = self.schema_dict.get('fields', {})
        defaults = self.schema_dict.get('defaults', {})

        self.clear_form()

        self.add_section_header('Auto-Metadata Generation')
        
        self.template_input = QLineEdit(filename_template)
        self.template_input.setPlaceholderText("e.g., {date}_{identifier}_{title}")
        self.template_input.setObjectName("formLineEdit")

        template_appended_label = QLabel("-000.tif")

        template_input_contianer = QWidget()
        template_input_layout = QHBoxLayout(template_input_contianer)
        template_input_layout.addWidget(self.template_input)
        template_input_layout.addWidget(template_appended_label)

        
        self.form_layout.addRow("<b>Filename Template:</b>", template_input_contianer)
        
        self.add_section_header('Fields (Variables)')
        for key, value in fields.items():
            if key == 'blank':
                for _ in range(int(value)):
                    self._field_row()
            else:
                self._field_row(key_name=key, field_type=value)
                
        self.add_section_header('Defaults (Internet Archive Templates)')
        for key, value in defaults.items():
            if key == 'blank':
                for _ in range(int(value)):
                    self._default_row()
            else:
                self._default_row(key, value)
                
    # --- Save Logic ---
    def _write_form_to_schema(self):
        new_fields = {}
        new_defaults = {}


        if hasattr(self, 'template_input') and self.template_input:
            self.schema_dict['filename_template'] = self.template_input.text().strip()

        for row in range(self.form_layout.rowCount()):
            label_item = self.form_layout.itemAt(row, QFormLayout.ItemRole.LabelRole)
            field_item = self.form_layout.itemAt(row, QFormLayout.ItemRole.FieldRole)

            if not field_item:
                continue
                
            widget = field_item.widget()

            # Check if it's a Custom Field Row (QWidget Container)
            if isinstance(widget, QWidget) and widget.layout():
                layout = widget.layout()
                if layout.count() == 2:
                    name_widget = layout.itemAt(0).widget()
                    type_widget = layout.itemAt(1).widget()
                    
                    if name_widget.property('role') == 'field_name':
                        field_name = name_widget.text().strip()
                        field_type = type_widget.currentText()
                        if field_name:
                            new_fields[field_name] = field_type

            # Check if it's a Default Template Row
            elif label_item:
                key_widget = label_item.widget()
                if isinstance(key_widget, QComboBox) and key_widget.property('role') == 'default_key':
                    key = key_widget.currentText().strip()
                    val = widget.text().strip()
                    if key:
                        new_defaults[key] = val

        self.schema_dict['fields'] = new_fields
        self.schema_dict['defaults'] = new_defaults

    def save(self):
        self._write_form_to_schema()
        # Clean up temporary 'blank' counters before saving
        self.schema_dict['fields'].pop('blank', None)
        self.schema_dict['defaults'].pop('blank', None)
        
        try:
            schema = DocumentSchema.from_dict(self.schema_dict)
            self.new_format.emit(schema)
        except Exception as e:
            self.error_window.emit(str(e))