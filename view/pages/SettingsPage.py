import sys, os, json
from PyQt6.QtWidgets import (
    QComboBox, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QCheckBox, QSpinBox, QDoubleSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt
from view.components import AnimatedToggle
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
        self._create_layout()
        
    def _create_layout(self):
        self.dynamic_widgets = {} 
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        lbl_title = QLabel("Application Settings")
        lbl_title.setObjectName("pageTitle")
        main_layout.addWidget(lbl_title)
        
        # --- Edit Schema Button --- 
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(15)

        if SessionManager.is_admin():
            schema_btn = QPushButton('Edit / Add Document Schema')
            schema_btn.setObjectName("infoBtn")
            schema_btn.clicked.connect(self.edit_document_schema)
            main_layout.addWidget(schema_btn)

            self.add_theme_switch()
            for key, value in self.current_settings.items():
                if key == 'THEME':
                    continue
                self.add_dynamic_setting(key,value)
            main_layout.addSpacing(20)
        else:
            self.add_theme_switch()
    
            
        main_layout.addLayout(self.form_layout)
        main_layout.addStretch()
        
        # --- Save Button ---
        btn_save = QPushButton("Save Settings")
        btn_save.setObjectName("successBtn")
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
                if not widget.isReadOnly():
                    app_settings.set(key, widget.text())

        app_settings.save()
        QMessageBox.information(self, "Success", "Settings saved successfully.")
    
    def edit_document_schema(self):
        print('edit schema pressed')
        self.new_window = self.parent.SchemaEditPage()
        self.new_window.setWindowTitle("Edit Document Schema")
        self.new_window.show()

    def add_dynamic_setting(self,key, value):
        label_text = key.replace('_', ' ').title() + ":"
        if isinstance(value, bool):
            widget = AnimatedToggle()
            widget.setChecked(value)
            
        elif isinstance(value, int):
            widget = QSpinBox()
            widget.setRange(0, 99999) 
            widget.setValue(value)
            widget.setObjectName("formSpinBox")
            
        elif isinstance(value, float):
            widget = QDoubleSpinBox()
            widget.setRange(0.0, 99999.0)
            widget.setValue(value)
            widget.setObjectName("formSpinBox")
            
        elif isinstance(value, str):
            widget = QLineEdit(value)
            widget.setObjectName("formLineEdit")
            
            # Hide text if it looks like a password or token
            if "key" in key.lower() or "token" in key.lower() or "password" in key.lower():
                widget.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
                
        else:
            # Fallback for complex types
            widget = QLineEdit(str(value))
            widget.setReadOnly(True)
            widget.setObjectName("formLineEdit")
            widget.setToolTip("Complex data type. Edit JSON directly.")
            # Give it a visual cue that it's disabled
            widget.setStyleSheet("color: #888888; background-color: transparent;") 

        self.dynamic_widgets[key] = widget
        self.form_layout.addRow(label_text, widget)

    def add_theme_switch(self):
        label_text = 'Theme'
        widget = QComboBox()
        widget.addItems(qdarktheme.get_themes())
        widget.setCurrentText(app_settings.get("THEME", "auto"))
        widget.setObjectName("formComboBox")
        widget.currentTextChanged.connect(setup_theme)
        self.dynamic_widgets['THEME'] = widget
        self.form_layout.addRow(label_text, widget)