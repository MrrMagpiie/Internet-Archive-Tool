import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget,QMainWindow, QGridLayout, 
    QSizePolicy, QSpacerItem, QFrame, QLabel,QListWidget,
    QListWidgetItem,QStyle
)
from PyQt6.QtCore import pyqtSlot,pyqtSignal, QSize, QObject, Qt
from PyQt6.QtGui import QFont,QIcon, QColor, QCursor,QPixmap,QPainter


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
        self.views = {}
        # Start
        self._create_layout()


    def _create_layout(self):
        self.setWindowTitle("School Archive Digitization Pipeline")
        self.resize(1200, 800)
        
        # Main Layout container
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- 1. THE SIDEBAR CONTAINER ---
        self.sidebar_container = QFrame()
        self.sidebar_container.setFixedWidth(280)
        self.sidebar_container.setStyleSheet("background-color: #2d2d2d; border: none;")
        
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # --- A. The App Logo & Title Area ---
        brand_widget = QWidget()
        brand_widget.setFixedHeight(100) # Fixed height for the header
        brand_layout = QHBoxLayout()
        brand_layout.setContentsMargins(20, 20, 20, 20)
        
        # The Logo (Drawing a circle placeholder for now)
        logo_lbl = QLabel()
        logo_lbl.setFixedSize(40, 40)
        logo_pixmap = QPixmap(40, 40)
        logo_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(logo_pixmap)
        painter.setBrush(QColor("#007acc")) # Archive Blue
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 40, 40)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        painter.drawText(0, 0, 40, 40, Qt.AlignmentFlag.AlignCenter, "A") # "A" for Archive
        painter.end()
        logo_lbl.setPixmap(logo_pixmap)
        
        # The Title Text
        title_lbl = QLabel("Archive\nPipeline")
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #ffffff;")
        
        brand_layout.addWidget(logo_lbl)
        brand_layout.addSpacing(10)
        brand_layout.addWidget(title_lbl)
        brand_layout.addStretch()
        brand_widget.setLayout(brand_layout)
        
        sidebar_layout.addWidget(brand_widget)
        
        # --- B. The Navigation Menu ---
        self.sidebar_list = QListWidget()
        self.sidebar_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sidebar_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                color: #cccccc;
                font-size: 14px;
                outline: 0;
            }
            QListWidget::item {
                padding: 12px 20px;
                border-left: 4px solid transparent;
            }
            QListWidget::item:hover {
                background-color: #383838;
                color: white;
            }
            QListWidget::item:selected {
                background-color: #383838;
                color: white;
                border-left: 4px solid #007acc; /* The "Active" accent line */
            }
        """)
        
        # 1. Dashboard (Icon: Computer)
        self.add_menu_item(" Documents", QStyle.StandardPixmap.SP_ComputerIcon)
        
        # 2. Acquisition (Icon: File Icon)
        self.add_menu_item(" Review", QStyle.StandardPixmap.SP_FileIcon)
        
        # 3. Processing (Icon: Browser/View)
        self.add_menu_item(" Settings", QStyle.StandardPixmap.SP_FileDialogDetailedView)
        
        # 4. Upload (Icon: Up Arrow)
        self.add_menu_item(" Help", QStyle.StandardPixmap.SP_ArrowUp)

        sidebar_layout.addWidget(self.sidebar_list)
        
        # --- C. Bottom "Settings" or Version Area ---
        version_lbl = QLabel("v1.0.4 Beta")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_lbl.setStyleSheet("color: #555; padding: 10px; font-size: 11px;")
        sidebar_layout.addWidget(version_lbl)

        self.sidebar_container.setLayout(sidebar_layout)
        
        # --- 2. THE STACKED PAGES ---
        self.stack = QStackedWidget()
        self._create_pages() 
        
        # Connect Sidebar to Pages
        self.sidebar_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar_list.setCurrentRow(0)
        
        # Assemble Main Layout
        main_layout.addWidget(self.sidebar_container)
        main_layout.addWidget(self.stack)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def add_menu_item(self,name, icon_enum):
            item = QListWidgetItem(name)
            # Use built-in Qt Standard Pixmaps for icons
            std_icon = self.style().standardIcon(icon_enum)
            item.setIcon(std_icon)
            self.sidebar_list.addItem(item)

    def _create_pages(self):
        self._main_dashboard()
        self._review_page()
        self._settings_page()
        self._help_page()

    def _main_dashboard(self):
        self.dashboard = self.gui_manager.DashboardPage(self.stack)
        self.stack.addWidget(self.dashboard)
        self.views['dashboard'] = self.dashboard

    def _settings_page(self):
        # main batch Dashboard
        self.step_dashboard = self.gui_manager.SettingsPage()
        self.stack.addWidget(self.step_dashboard)
        self.views['batch_dashboard'] = self.step_dashboard
        
    def _review_page(self):
        self.single_doc = self.gui_manager.SingleDocumentPage()
        self.stack.addWidget(self.single_doc)
        self.views['single_doc'] = self.single_doc

    def _help_page(self):
        self.settings = self.gui_manager.SettingsPage()
        self.stack.addWidget(self.settings)
        self.views['settings'] = self.settings

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

    '''
    removed to be replaced with new version
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
        '''




# ---------------- Entry Point ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())