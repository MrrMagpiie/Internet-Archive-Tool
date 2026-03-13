from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QLabel, QPushButton, 
    QFrame, QScrollArea, QSizePolicy, QButtonGroup # <--- NEW: Import QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QObject
from PyQt6.QtGui import QFont, QCursor

class NavigationBar(QFrame):
    def __init__(self, back_callback, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setObjectName("workflowNavBar")
        
        self.nav_layout = QHBoxLayout()
        self.buttons = {}
        
        # --- NEW: The Invisible Manager ---
        # Passing 'self' ensures it gets garbage collected when the nav bar closes
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True) 
        
        self.btn_back = QPushButton("← All Projects")
        self.btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_back.setObjectName("workflowBackBtn")
        
        if back_callback:
            self.btn_back.clicked.connect(back_callback)
        
        # Project Title (Dynamic)
        self.page_title = QLabel("Example Title")
        self.page_title.setObjectName("workflowTitle")
        
        # Assemble Nav Bar
        self.nav_layout.addWidget(self.btn_back)
        self.nav_layout.addSpacing(20)
        self.nav_layout.addWidget(self.page_title)
        self.nav_layout.addStretch() 
        
        self.setLayout(self.nav_layout)

    def add_button(self, text, btn_id, callback=None):
        """Adds a new stepper button to the right side of the nav bar."""
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setObjectName("workflowStepBtn") 
        
        # Connect the external logic directly
        if callback:
            btn.clicked.connect(callback)
            
        # Store for programmatic access later
        self.buttons[str(btn_id)] = btn
        self.nav_layout.addWidget(btn)
        
        # --- NEW: Hand the button over to the manager ---
        self.button_group.addButton(btn)

    def set_title(self, title_text):
        """Helper to quickly update the title string."""
        self.page_title.setText(str(title_text))

    def set_active(self, btn_id):
        """Allows parent pages to programmatically change the active button."""
        safe_id = str(btn_id)
        if safe_id in self.buttons:
            self.buttons[safe_id].setChecked(True)