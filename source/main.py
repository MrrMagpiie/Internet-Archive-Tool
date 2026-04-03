import sys
import multiprocessing
from PyQt6.QtWidgets import (
    QApplication, QDialog)
from controller.GUIManager import GUIManager
from controller.ProcessManager import ProcessManager
from model.logic.app_setup import init_app_environment
from model.settings_manager import app_settings

def main():
    init_app_environment()
    app_settings.load()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    process_manager = ProcessManager()
    gui_manager = GUIManager(process_manager)
    gui_manager.setup_theme()
    need_setup = process_manager.check_setup()
    
    if any(need_setup):
        wizard = gui_manager.create_setup_wizard(need_setup)
        wizard.show()
        result = wizard.exec()     
        if result == QDialog.DialogCode.Rejected:
            process_manager.closeEvent()
            sys.exit()
    
    login = gui_manager.create_login_page()
    login.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
        
    
    