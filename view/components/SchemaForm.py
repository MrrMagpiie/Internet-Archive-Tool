import os
from PyQt6.QtWidgets import (
    QWidget, QTextEdit, QLineEdit,
    QTableWidget,QComboBox,QLabel,QFormLayout
)
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from model.data.schema import DocumentSchema
from model.data.metadata import Metadata


class SchemaForm(QWidget):
    def __init__(self):
        super().__init__()
        self.form_layout = QFormLayout(self)
        self.current_schema: DocumentSchema = None
 
    def _build_form(self,fields):
        self.clear_layout(self.form_layout)
        if isinstance(fields,dict):
            for key,value in fields.items():
                    label = QLabel(key)
                    self.form_layout.addRow(label, QLineEdit())
        '''else:
            label = QLabel(fields)
            self.form_layout.addRow(label,QLineEdit())'''

    @pyqtSlot(dict)
    def new_form(self,schema_format:dict):
        self.current_schema = DocumentSchema.from_dict(schema_format)
        fields = schema_format.get("fields")
        self._build_form(fields)
    
    @pyqtSlot()
    def clear_layout(self, layout):
        """Removes all widgets from a layout and schedules them for deletion."""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

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

        
