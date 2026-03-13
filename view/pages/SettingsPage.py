import sys, os, json
from PyQt6.QtWidgets import (
    QComboBox, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QCheckBox, QSpinBox, QDoubleSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt

from view.components.Page import Page
from view.components.SchemaForm import *
from view.pages.SchemaEditPage import SchemaEditPage
from model.settings_manager import app_settings
import qdarktheme
from model.logic.helpers import setup_theme
from model.service.SessionManager import SessionManager

class SettingsPage(Page):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_settings = app_settings.get_all()
        self.create_layout()
        
    def create_layout(self):
        self.dynamic_widgets = {} 
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        lbl_title = QLabel("Application Settings")
        lbl_title.setObjectName("pageTitle") # REUSED: Global Typography Hook
        main_layout.addWidget(lbl_title)
        
        # --- Edit Schema Button --- 
        form_layout = QFormLayout()
        form_layout.setSpacing(15)

        if SessionManager.is_admin():
            schema_btn = QPushButton('Edit / Add Document Schema')
            schema_btn.setObjectName("infoBtn") # REUSED: Global Blue Button
            schema_btn.clicked.connect(self.edit_document_schema)
            main_layout.addWidget(schema_btn)

            # Give it a little breathing room before the form
            main_layout.addSpacing(20)

            # --- The Dynamic Form ---
            
            
            for key, value in self.current_settings.items():
                # 1. Format the label (e.g., "ia_api_key" -> "Ia Api Key")
                label_text = key.replace('_', ' ').title() + ":"
                
                # 2. Determine Widget by Type
                if key == 'THEME':
                    widget = QComboBox()
                    widget.addItems(qdarktheme.get_themes())
                    widget.setCurrentText(app_settings.get("THEME", "auto"))
                    widget.setObjectName("formComboBox") # REUSED: Form Hook
                    widget.currentTextChanged.connect(setup_theme)

                elif isinstance(value, bool):
                    widget = QCheckBox()
                    widget.setChecked(value)
                    # Checkboxes look great natively, no custom CSS ID needed!
                    
                elif isinstance(value, int):
                    widget = QSpinBox()
                    widget.setRange(0, 99999) 
                    widget.setValue(value)
                    widget.setObjectName("formSpinBox") # NEW: QSS Hook
                    
                elif isinstance(value, float):
                    widget = QDoubleSpinBox()
                    widget.setRange(0.0, 99999.0)
                    widget.setValue(value)
                    widget.setObjectName("formSpinBox") # NEW: QSS Hook
                    
                elif isinstance(value, str):
                    widget = QLineEdit(value)
                    widget.setObjectName("formLineEdit") # REUSED: Form Hook
                    
                    # Hide text if it looks like a password or token
                    if "key" in key.lower() or "token" in key.lower() or "password" in key.lower():
                        widget.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
                        
                else:
                    # Fallback for complex types
                    widget = QLineEdit(str(value))
                    widget.setReadOnly(True)
                    widget.setObjectName("formLineEdit") # REUSED: Form Hook
                    widget.setToolTip("Complex data type. Edit JSON directly.")
                    # Give it a visual cue that it's disabled
                    widget.setStyleSheet("color: #888888; background-color: transparent;") 

                self.dynamic_widgets[key] = widget
                form_layout.addRow(label_text, widget)

        else:
            key = 'THEME'
            label_text = key.replace('_', ' ').title() + ":"
            widget = QComboBox()
            widget.addItems(qdarktheme.get_themes())
            widget.setCurrentText(app_settings.get("THEME", "auto"))
            widget.setObjectName("formComboBox") # REUSED: Form Hook
            widget.currentTextChanged.connect(setup_theme)
            self.dynamic_widgets[key] = widget
            form_layout.addRow(label_text, widget)
                

            # 3. Store the widget reference and add it to the UI
    
            
        main_layout.addLayout(form_layout)
        main_layout.addStretch()
        
        # --- Save Button ---
        btn_save = QPushButton("Save Settings")
        btn_save.setObjectName("successBtn") # REUSED: Global Green Button
        btn_save.clicked.connect(self.save_settings)
        main_layout.addWidget(btn_save)
        
        self.setLayout(main_layout)

    # --- The Dynamic Save Function ---
    def save_settings(self):
        # Loop through stored widgets and extract the data based on type
        for key, widget in self.dynamic_widgets.items():
            if isinstance(widget, QCheckBox):
                app_settings.set(key, widget.isChecked())
            elif isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                app_settings.set(key, widget.value())
            elif isinstance(widget, QComboBox):
                app_settings.set(key, widget.currentText())
            elif isinstance(widget, QLineEdit):
                # FIXED: Prevent data corruption by ignoring read-only fallbacks!
                if not widget.isReadOnly():
                    app_settings.set(key, widget.text())

        app_settings.save()
        QMessageBox.information(self, "Success", "Settings saved successfully.")
    
    def edit_document_schema(self):
        print('edit schema pressed')
        self.new_window = self.parent.SchemaEditPage()
        self.new_window.show()