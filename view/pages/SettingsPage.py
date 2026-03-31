import sys, os,json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QCheckBox, QSpinBox, QDoubleSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt

from view.components import ActionCard
from view.components.ActionDashboard import ActionDashboard
from view.components.Page import Page
from view.components.SchemaForm import *
from view.pages.SchemaEditPage import SchemaEditPage
from model.settings_manager import app_settings



class SettingsPage(Page):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.current_settings = app_settings.get_all()
        self.create_layout()
        
    def create_layout(self):
        
        # This will map the JSON key to the PyQt Widget
        # e.g., {"ia_api_key": <QLineEdit object>}
        self.dynamic_widgets = {} 
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        lbl_title = QLabel("Application Settings")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        main_layout.addWidget(lbl_title)
        
        # --- Edit Schema Schema --- 
        schema_btn = QPushButton('Edit/Add Document Schema')
        schema_btn.clicked.connect(self.edit_document_schema)
        main_layout.addWidget(schema_btn)

        # --- The Dynamic Form ---
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        for key, value in self.current_settings.items():
            # 1. Format the label (e.g., "ia_api_key" -> "Ia Api Key")
            label_text = key.replace('_', ' ').title() + ":"
            
            # 2. Determine Widget by Type
            if isinstance(value, bool):
                widget = QCheckBox()
                widget.setChecked(value)
                
            elif isinstance(value, int):
                widget = QSpinBox()
                widget.setRange(0, 99999) 
                widget.setValue(value)
                
            elif isinstance(value, float):
                widget = QDoubleSpinBox()
                widget.setRange(0.0, 99999.0)
                widget.setValue(value)
                
            elif isinstance(value, str):
                widget = QLineEdit(value)
                
                # Hide text if it looks like a password or token
                if "key" in key.lower() or "token" in key.lower() or "password" in key.lower():
                    widget.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
                    
            else:
                # Fallback for complex types (lists, dicts) - just show as string
                widget = QLineEdit(str(value))
                widget.setReadOnly(True)
                widget.setToolTip("Complex data type. Edit JSON directly.")

            # 3. Store the widget reference and add it to the UI
            self.dynamic_widgets[key] = widget
            form_layout.addRow(label_text, widget)
            
        main_layout.addLayout(form_layout)
        main_layout.addStretch()
        
        # --- Save Button ---
        btn_save = QPushButton("Save Settings")
        btn_save.setStyleSheet("background-color: #2da44e; color: white; padding: 10px;")
        btn_save.clicked.connect(self.save_settings)
        main_layout.addWidget(btn_save)
        
        self.setLayout(main_layout)

    # --- The Dynamic Save Function ---
    def save_settings(self):
        new_settings = {}
        
        # Loop through stored widgets and extract the data based on type
        for key, widget in self.dynamic_widgets.items():
            if isinstance(widget, QCheckBox):
                app_settings.set(key, widget.isChecked())
            elif isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                app_settings.set(key, widget.value())
                #new_settings[key] = widget.value()
            elif isinstance(widget, QLineEdit):
                app_settings.set(key, widget.text())
                #new_settings[key] = widget.text()

        app_settings.save()
        
        # Call your config.py save function here
        # save_config(new_settings)
        
        QMessageBox.information(self, "Success", "Settings saved successfully.")
    
    def edit_document_schema(self):
        print('edit schema pressed')
        self.new_window = self.parent.SchemaEditPage()
        self.new_window.show()