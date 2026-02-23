import sys, os,json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QCheckBox, QSpinBox, QDoubleSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt

from view.components.ActionCard import ActionCard
from view.components.ActionDashboard import ActionDashboard
from view.components.Page import Page
from config import SETTINGS_PATH

class SettingsPage(Page):
    def __init__(self, config_dict,parent=None):
        super().__init__(parent)
        self.current_settings = self.load_settings()
        
        # This will map the JSON key to the PyQt Widget
        # e.g., {"ia_api_key": <QLineEdit object>}
        self.dynamic_widgets = {} 
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        lbl_title = QLabel("Application Settings")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        main_layout.addWidget(lbl_title)
        
        # --- The Dynamic Form ---
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        for key, value in self.current_settings.items():
            # 1. Format the label (e.g., "ia_api_key" -> "Ia Api Key")
            label_text = key.replace('_', ' ').title() + ":"
            
            # 2. Determine Widget by Type
            # Note: In Python, bool is a subclass of int, so check bool FIRST!
            if isinstance(value, bool):
                widget = QCheckBox()
                widget.setChecked(value)
                
            elif isinstance(value, int):
                widget = QSpinBox()
                widget.setRange(0, 99999) # Set a wide generic range
                widget.setValue(value)
                
            elif isinstance(value, float):
                widget = QDoubleSpinBox()
                widget.setRange(0.0, 99999.0)
                widget.setValue(value)
                
            elif isinstance(value, str):
                widget = QLineEdit(value)
                
                # UX Heuristic: Hide text if it looks like a password or token
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
        
        # Loop through our stored widgets and extract the data based on type
        for key, widget in self.dynamic_widgets.items():
            if isinstance(widget, QCheckBox):
                new_settings[key] = widget.isChecked()
            elif isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
                new_settings[key] = widget.value()
            elif isinstance(widget, QLineEdit):
                new_settings[key] = widget.text()

        print("New Settings to save:", new_settings)
        
        with open(SETTINGS_PATH, "w") as f:
            json.dump(new_settings, f, indent=4)
        
        # Call your config.py save function here
        # save_config(new_settings)
        
        QMessageBox.information(self, "Success", "Settings saved successfully.\nYou will need to restart the program for changes to take effect")

    def load_settings(self):
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, "r") as f:
                return json.load(f)
        return default_settings
    
    