import json
from PyQt6.QtWidgets import (
    QComboBox, QVBoxLayout, QLineEdit,
    QPushButton, QFormLayout, QCheckBox,
    QSpinBox, QDoubleSpinBox, QMessageBox,
)
from PyQt6.QtCore import Qt
from view.components import AnimatedToggle,Page
from model.settings_manager import app_settings
import qdarktheme
from model.service.SessionManager import SessionManager

class SettingsPage(Page):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dynamic_widgets = {}
        self.current_settings = app_settings.get_all()
        self._create_layout()

    def _create_layout(self):
        settings_layout = QVBoxLayout(self)
        
        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(15)

        if SessionManager.is_admin():
            self.add_theme_switch()
            for key, value in self.current_settings.items():
                if key == 'THEME':
                    continue
                self.add_dynamic_setting(key,value)
            settings_layout.addSpacing(20)
        else:
            self.add_theme_switch()
    
            
        settings_layout.addLayout(self.form_layout)
        settings_layout.addStretch()
        
        # --- Save Button ---
        btn_save = QPushButton("Save Settings")
        btn_save.setObjectName("successBtn")
        btn_save.clicked.connect(self.save_settings)
        settings_layout.addWidget(btn_save)

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
        widget.currentTextChanged.connect(self.parent.setup_theme)
        self.dynamic_widgets['THEME'] = widget
        self.form_layout.addRow(label_text, widget)




