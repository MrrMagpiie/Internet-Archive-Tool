import sys
from PyQt6.QtWidgets import (
    QApplication)
from controller.GUIManager import GUIManager
from controller.ProcessManager import ProcessManager
from model.logic.app_setup import init_app_environment
from model.settings_manager import app_settings
from model.logic.helpers import setup_theme






if __name__ == "__main__":
    init_app_environment()
    app_settings.load()
    app = QApplication(sys.argv)
    setup_theme()
    app.setQuitOnLastWindowClosed(False)
    manager = ProcessManager()
    guimanager = GUIManager(manager)
    manager.check_setup()
        
    sys.exit(app.exec())
    