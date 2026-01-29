import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QStackedWidget, QLabel, QPushButton, QSplitter, 
    QListWidgetItem, QFrame, QFormLayout, QLineEdit, QDateEdit,
    QProgressBar, QComboBox, QGraphicsView, QGraphicsScene,QGridLayout,
    QScrollArea,QSizePolicy, QLayout
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QRect, QPoint, pyqtSlot
from PyQt6.QtGui import QIcon, QFont, QColor, QCursor

from view.components.Page import Page
from view.components.CenteredFlowLayout import CenteredFlowLayout
from view.components.DashboardDocumentCard import DocumentCard

class NewCard(QFrame):
    clicked = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Dashed Border Style
        self.setStyleSheet("""
            NewCard {
                background-color: #f8f9fa;
                border: 2px dashed #d1d5da;
                border-radius: 8px;
            }
            NewCard:hover {
                background-color: #f0f3f6;
                border-color: #0366d6;
            }
        """)
        
        # Center the content
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # The Plus Icon (Using text for simplicity, could be an SVG)
        icon_lbl = QLabel("+")
        icon_lbl.setStyleSheet("color: #586069; font-weight: 300; background: transparent; border: none;")
        icon_lbl.setFont(QFont("Segoe UI", 40))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # The Text
        text_lbl = QLabel("New Document")
        text_lbl.setStyleSheet("color: #586069; font-weight: bold; background: transparent; border: none;")
        text_lbl.setFont(QFont("Segoe UI", 11))
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl)
        
        self.setLayout(layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            print("Create New Document Emit")
            self.clicked.emit('new_document')
        super().mousePressEvent(event)

class DashboardController(Page):
    def __init__(self,navigation_stack,parent):
        super().__init__(parent=parent)
        
        # This layout holds the "Swap" logic
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        
        # --- View 1: The Grid (Existing ProjectListView) ---
        # Note: I renamed your previous ProjectListView class to 'ProjectListView' 
        # for clarity.
        self.project_list_view = ProjectListView(self) 
        self.project_list_view.project_selected.connect(self.open_project)
        
        # --- View 2: The Workflow ---
        self.workflow_view = ProjectWorkflowView(parent=parent)
        self.workflow_view.back_to_dashboard.connect(self.close_project)
        
        self.stack.addWidget(self.project_list_view) # Index 0
        self.stack.addWidget(self.workflow_view)     # Index 1
        
        self.layout.addWidget(self.stack)
        self.setLayout(self.layout)

    def open_project(self, project_name):
        print(f"Opening {project_name}...")
        self.workflow_view.load_project(project_name)
        
        # Animate/Swap to the workflow view
        self.stack.setCurrentIndex(1) 

    def close_project(self):
        # Swap back to the grid
        self.stack.setCurrentIndex(0)

class ProjectWorkflowView(Page):
    # Signal to go back to the Project Grid
    back_to_dashboard = pyqtSignal()

    def __init__(self,parent):
        super().__init__(parent)
        self._create_layout()
        
    def _create_layout(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # --- 1. Top Navigation Bar (The "Stepper") ---
        nav_bar = QFrame()
        nav_bar.setFixedHeight(60)
        nav_bar.setStyleSheet("background-color: #f6f8fa; border-bottom: 1px solid #d1d5da;")
        nav_layout = QHBoxLayout()
        
        # "Back" Button
        btn_back = QPushButton("← All Projects")
        btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_back.setStyleSheet("border: none; color: #586069; font-weight: bold;")
        btn_back.clicked.connect(self.return_to_dashboard)
        
        # Project Title (Dynamic)
        self.lbl_project_title = QLabel("Example Title")
        self.lbl_project_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        
        # Stage Switcher (Segmented Control)
        # In a real app, these would be checkable buttons in a QButtonGroup
        self.btn_scan = QPushButton("1. Files")
        self.btn_process = QPushButton("2. Metadata")
        self.btn_upload = QPushButton("3. Review")
        
        for btn in [self.btn_scan, self.btn_process, self.btn_upload]:
            btn.setCheckable(True)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton { border: none; padding: 5px 15px; color: #586069; font-weight: 600; }
                QPushButton:checked { color: #0366d6; border-bottom: 2px solid #0366d6; }
                QPushButton:hover { color: #0366d6; }
            """)
            
        # Connect buttons to switch pages
        self.btn_scan.clicked.connect(lambda: self.switch_stage(0))
        self.btn_process.clicked.connect(lambda: self.switch_stage(1))
        self.btn_upload.clicked.connect(lambda: self.switch_stage(2))

        # Assemble Nav Bar
        nav_layout.addWidget(btn_back)
        nav_layout.addSpacing(20)
        nav_layout.addWidget(self.lbl_project_title)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_scan)
        nav_layout.addWidget(self.btn_process)
        nav_layout.addWidget(self.btn_upload)
        nav_bar.setLayout(nav_layout)
        
        layout.addWidget(nav_bar)
        
        
        # --- 2. The Internal Stack (The Stages) ---
        self.stage_stack = QStackedWidget()
        self._create_pages()
        
        layout.addWidget(self.stage_stack)
        self.setLayout(layout)
        
        # Default to Scan
        self.switch_stage(0)
    
    def _create_pages(self):
        create_doc_page = self.parent.CreateDocumentPage()
        metadata_page = self.parent.MetadataPage()

        self.stage_stack.addWidget(create_doc_page) # Index 0
        self.stage_stack.addWidget(metadata_page)    # Index 1 
        pass    

    def load_project(self, project_name):
        """Called when entering this view"""
        if project_name == 'new_document':
            self.lbl_project_title.setText('New Document')
            self.switch_stage(0)
        else:
            self.lbl_project_title.setText(project_name)
            self.switch_stage(1) # Always start at Scan

    def switch_stage(self, index):
        print(f'Switching to Stage{index}')
        self.stage_stack.setCurrentIndex(index)
        
        # Update Button States manually (since they are custom styled)
        self.btn_scan.setChecked(index == 0)
        self.btn_process.setChecked(index == 1)
        self.btn_upload.setChecked(index == 2)

    def return_to_dashboard(self):
        print('Return to Dashboard')
        self.back_to_dashboard.emit()

class ProjectListView(Page):
    project_selected = pyqtSignal(str)
    def __init__(self,parent):
        super().__init__(parent=parent)
        
        # Main Layout of the Page
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(40)
        # Header Section
        title = QLabel("Dashboard")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        
        main_layout.addWidget(title)
        new_card = NewCard()
        new_card.clicked.connect(self.card_clicked)
        main_layout.addWidget(new_card)
        
        recent_docects_header = QLabel("Recent Documents")
        recent_docects_header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        main_layout.addWidget(recent_docects_header)

        # --- The Scroll Area for the Grid ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background-color: transparent;") # Let window bg show
        # --- The Scroll Area for the Grid ---

       
        # The container widget that holds the grid
        grid_container = QWidget()
        
        self.layout_flow = CenteredFlowLayout()  
        self.layout_flow.setSpacing(20)
        self.layout_flow.setContentsMargins(20, 20, 20, 20)   # <-- ADD THIS (pass margins if needed)
        
        grid_container.setLayout(self.layout_flow)
        scroll_area.setWidget(grid_container)
        
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
        example_docs = [
            {"title": "1985 Yearbook", "status": "Ready for Upload", "prog": 100, "color": "#2da44e"},
            {"title": "1950 Newspaper", "status": "Processing: Deskew", "prog": 45, "color": "#d29922"},
            {"title": "1992 Yearbook", "status": "Scanning (Page 12)", "prog": 10, "color": "#0969da"},
            {"title": "1992 Yearbook v2", "status": "Scanning (Page 4)", "prog": 2, "color": "#0969da"},
            {"title": "1940 Journal", "status": "Ready", "prog": 100, "color": "#2da44e"},
        ]
        self.show_documents(example_docs)

    @pyqtSlot(str)
    def card_clicked(self,title):
        if title == 'new_document':
            print('Create New Document Clicked')
        else:
            print(f'{title} Card Clicked')
        self.project_selected.emit(title)

    @pyqtSlot(list)
    def show_documents(self,docs):
                # --- Mock Data Generation ---
        for doc in docs:
            card = DocumentCard(doc["title"], doc["status"], doc["prog"], doc["color"])
            card.clicked.connect(self.card_clicked)
            # Just add widget, no row/col coordinates needed anymore!
            self.layout_flow.addWidget(card)