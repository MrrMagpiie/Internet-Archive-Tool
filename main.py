import sys
from PyQt6.QtWidgets import (
    QApplication)
from controller.GUIManager import GUIManager
from controller.ProcessManager import ProcessManager

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    manager = ProcessManager()
    guimanager = GUIManager(manager)
    manager.need_setup.connect(guimanager.run_setup)
    window = guimanager.MainWindow()
    window.show()
    sys.exit(app.exec())