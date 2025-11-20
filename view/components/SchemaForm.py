import os
from PyQt6.QtWidgets import (
    QWidget, QTextEdit, QLineEdit,
    QTableWidget,QComboBox,QLabel,QFormLayout
)
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot



class SchemaForm(QWidget):
    def __init__(self):
        super().__init__()
        self.form_layout = QFormLayout(self)
 
    def _build_form(self,fields):
        self.clear_layout(self.form_layout)
        if isinstance(fields,dict):
            for key,value in fields.items():
                if isinstance(value,dict):
                    for subkey, subvalue in value.items():
                        label = QLabel(subkey)
                        self.form_layout.addRow(label, QLineEdit())
                else: 
                    label = QLabel(key)
                    self.form_layout.addRow(label, QLineEdit())
        else:
            label = QLabel(fields)
            self.form_layout.addRow(label,QLineEdit())

    @pyqtSlot(dict)
    def new_form(self,format:dict):
            fields = format.get("fields")
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
