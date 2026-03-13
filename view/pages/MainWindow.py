import sys
import qtawesome as qta
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QMainWindow, QFrame,
    QLabel, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import pyqtSignal, QSize, Qt
from PyQt6.QtGui import QFont, QColor, QPixmap, QPainter

from config import DEV_MODE
from model.settings_manager import app_settings
from model.service.SessionManager import SessionManager
from view.pages.LoginPage import LoginPage



def build_logo():
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
    painter.drawText(0, 0, 40, 40, Qt.AlignmentFlag.AlignCenter, "A")
    painter.end()
    logo_lbl.setPixmap(logo_pixmap)
    return logo_lbl

def build_brand_widget():
    brand_widget = QWidget()
    brand_widget.setObjectName("brandWidget") # NEW: Hook for QSS
    brand_widget.setFixedHeight(100)
    brand_layout = QHBoxLayout()
    brand_layout.setContentsMargins(20, 20, 20, 20)

    status_icon_label = QLabel()
    my_icon = qta.icon(
        "mdi.bookshelf", 
        color=  "#4CAF50",
        scale_factor=1.7,
    )
    status_icon_label.setPixmap(my_icon.pixmap(QSize(24, 24)))

    brand_layout.addWidget(status_icon_label)
    title_lbl = QLabel("Archive Pipeline")
    title_lbl.setObjectName("brandTitleLabel") # NEW: Hook for QSS
    
    brand_layout.addSpacing(10)
    brand_layout.addWidget(title_lbl)
    brand_layout.addStretch()
    brand_widget.setLayout(brand_layout)
    return brand_widget



# ---------------- Main UI ----------------
class MainWindow(QMainWindow):
    main_window_ready = pyqtSignal()
    
    def __init__(self, parent):
        super().__init__()
        self.setMinimumSize(QSize(100, 600)) 
        self.gui_manager = parent
        self.views = {}
        # Start
        self._create_layout()

    def _create_layout(self):
        if DEV_MODE:
            self.setWindowTitle("Development: Archive Digitization Pipeline")
        else:
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
        self.sidebar_container.setObjectName("sidebarContainer") # NEW: Hook for QSS
        
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # --- A. The App Logo & Title Area ---
        brand_widget = build_brand_widget()
        
        # --- B. The Navigation Menu ---
        self.sidebar_list = QListWidget()
        self.sidebar_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sidebar_list.setObjectName("sidebarList") # NEW: Hook for QSS
        
        self.setIconSize(QSize(30, 30))
        

        # --- Process Manager Widget ---
        self.process_manager_widget = self.gui_manager.ProcessManagerWidget()
        

        # --- C. Bottom Version Area ---
        version_lbl = QLabel("v0.0.1")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_lbl.setObjectName("versionLabel") # NEW: Hook for QSS
        
        
        # --- 2. THE STACKED PAGES ---
        self.stack = QStackedWidget()
        self._create_pages() 
        
        # Connect Sidebar to Pages
        self.sidebar_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar_list.setCurrentRow(0)
        
        # Assemble Main Layout
        
        sidebar_layout.addWidget(brand_widget)
        sidebar_layout.addWidget(self.sidebar_list)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.process_manager_widget)
        sidebar_layout.addWidget(version_lbl)
        self.sidebar_container.setLayout(sidebar_layout)


        main_layout.addWidget(self.sidebar_container)
        main_layout.addWidget(self.stack)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def add_menu_item(self, name, icon_enum):
        item = QListWidgetItem(name)
        std_icon = self.style().standardIcon(icon_enum)
        item.setIcon(std_icon)
        self.sidebar_list.addItem(item)

    def _create_pages(self):
        self._main_dashboard()
        if SessionManager.is_admin() or not app_settings.get('ADMIN_UPLOAD'):
            self._review_page()
        self._settings_page()
        self._help_page()
    
    def add_menu_item(self, name, icon_enum):
        item = QListWidgetItem(name)
        my_icon = qta.icon(
            icon_enum, 
            color="#cccccc",         # Your unselected text color
            color_active="#4CAF50",
            scale_factor=1.2,       # Your blue 'selected' accent color
        )
        
        item.setIcon(my_icon)
        item = QListWidgetItem(name)
        self.sidebar_list.addItem(item)

    # ---------------- Pages ----------------

    def _main_dashboard(self):
        self.dashboard = self.gui_manager.DashboardPage(self.stack)
        self.stack.addWidget(self.dashboard)
        self.views['dashboard'] = self.dashboard
        self.add_menu_item("Document", "mdi.file-document-edit")

    def _settings_page(self):
        self.settings = self.gui_manager.SettingsPage()
        self.stack.addWidget(self.settings)
        self.views['settings'] = self.settings
        self.add_menu_item("Settings", "fa5s.cog")
        
        
    def _review_page(self):
        self.review = self.gui_manager.ReviewPage()
        self.review.request_ready_documents()
        self.review.request_uploaded_documents()
        self.stack.addWidget(self.review)
        self.views['review'] = self.review
        self.add_menu_item("Upload", "fa5s.file-upload")

    def _help_page(self):
        self.help = self.gui_manager.HelpPage()
        self.stack.addWidget(self.help)
        self.views['help'] = self.help
        self.add_menu_item("Help", "mdi.help-circle-outline")
    
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
    # Passed None temporarily to bypass crash in standalone test
    window = MainWindow(None) 
    window.show()
    sys.exit(app.exec())