import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget,QMainWindow, QGridLayout, 
    QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import pyqtSlot,pyqtSignal, QSize, QObject
from PyQt6.QtGui import QFont

#import pages
from view.pages import *

# ---------------- Main UI ----------------
class MainWindow(QMainWindow):
    main_window_ready = pyqtSignal()
    def __init__(self,parent):
        super().__init__()
        
        self.setWindowTitle("Archival Wizard")
        self.setMinimumSize(QSize(100, 600)) 
        self.gui_manager = parent
        self.config_path = Path("./Resources/ia.ini")    

        # Start
        self._create_layout()

    def _create_layout(self):
        self.stack = QStackedWidget()
        self.views = {}
        self._create_pages()
        
        # Global Back Button Setup
        self.back_button = QPushButton("Return to Dashboard")
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.back_button.setFixedSize(160, 35)
        self.back_button.setFont(QFont("Arial", 9))


        # Theme Switcher (Added for demonstration)
        self.theme_btn = QPushButton("🌙 Toggle Dark Mode")
        self.theme_btn.setObjectName("themeButton")
        self.theme_btn.setFixedSize(160, 35)
        self.theme_btn.setFont(QFont("Arial", 9))
        
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        top_bar = QHBoxLayout()
        top_bar.addSpacing(15)
        top_bar.addWidget(self.back_button)
        top_bar.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        top_bar.addWidget(self.theme_btn)
        top_bar.addSpacing(15)

        container_layout.addLayout(top_bar)
        container_layout.addWidget(self.stack)
    
        central_widget = QWidget()
        central_widget.setLayout(container_layout)
        self.setCentralWidget(central_widget)
        
    def _create_pages(self):
        self._main_dashboard()
        self._single_doc()
        self._step_dashboard()
        

    def _main_dashboard(self):
        self.dashboard = self.gui_manager.DashboardPage(self.stack)
        self.stack.addWidget(self.dashboard)
        self.views['dashboard'] = self.dashboard

    def _step_dashboard(self):
        # main batch Dashboard
        self.step_dashboard = self.gui_manager.StepDashboardPage()
        self.stack.addWidget(self.step_dashboard)
        self.views['batch_dashboard'] = self.step_dashboard
        
    def _single_doc(self):
        self.single_doc = self.gui_manager.SingleDocumentPage()
        self.stack.addWidget(self.single_doc)
        self.views['single_doc'] = self.single_doc

    @pyqtSlot(dict) # Connect this to your pipeline_finished signal
    def on_discovery_complete(self, documents):
        # will move to the correct metadata page when documents have been discovered
        #self.navigate_to_page(self.metadata_page)
        # update metadata display to show files discovered that need metadata
        pass
    @pyqtSlot(bool,str)
    def on_credentails_setup(self,sucess,msg):
        # if credential setup was sucessfull remove page
        # if fail then show msg and allow user to add creds again
        pass
    
    def closeEvent(self, event):
        """Ensure all threads are stopped before closing the window."""
        print("Closing application and cleaning up threads...")
        self.gui_manager.process_manager.closeEvent(event)
        event.accept()
        QApplication.instance().quit()



# ---------------- Entry Point ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())