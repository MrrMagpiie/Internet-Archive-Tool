from PyQt6.QtWidgets import (
    QVBoxLayout, QLabel, QTabWidget
)
from PyQt6.QtCore import Qt
from view.components import Page
from model.settings_manager import app_settings
from model.service.SessionManager import SessionManager

class ConfigsPage(Page):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_settings = app_settings.get_all()
        self._create_layout()

    def _create_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        lbl_title = QLabel("Application Settings")
        lbl_title.setObjectName("pageTitle")
        main_layout.addWidget(lbl_title)
        
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # --- Settings Tab ---
        self.settings_tab = self.parent.create_settings_page()
        self.tabs.addTab(self.settings_tab, "Settings")
        
        # --- Schema Tab & User Tab (Admins Only) ---
        if SessionManager.is_admin():
            # Embed SchemaEditPage directly in tab
            self.schema_tab = self.parent.create_schema_edit_page()
            self.tabs.addTab(self.schema_tab, "Schema")
            
            # Users Tab
            self.users_tab = self.parent.create_users_page()
            self.tabs.addTab(self.users_tab, "Users")
        
        self.setLayout(main_layout)