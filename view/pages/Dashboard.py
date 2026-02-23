import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QStackedWidget, QLabel, QPushButton, QSplitter, 
    QListWidgetItem, QFrame, QFormLayout, QLineEdit, QDateEdit,
    QProgressBar, QComboBox, QGraphicsView, QGraphicsScene,QGridLayout,
    QScrollArea,QSizePolicy, QLayout
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QRect, QPoint, pyqtSlot,QObject
from PyQt6.QtGui import QIcon, QFont, QColor, QCursor

from view.components.Page import Page
from view.components.CenteredFlowLayout import CenteredFlowLayout
from view.components.DashboardDocumentCard import DocumentCard
from model.data.document import Document
from model.logic.helpers import clear_layout
from model.service.signals import JobTicket


class NewCard(QFrame):
    clicked = pyqtSignal(object,int)
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
            self.clicked.emit(None,0)
        super().mousePressEvent(event)

class DashboardPage(Page):
    db_request = pyqtSignal(dict,object)
    def __init__(self,parent,list_view,workflow_view):
        super().__init__(parent=parent)
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        
        # --- View 1: The Grid (Existing ListView) ---
        self.list_view = list_view
        self.list_view.project_selected.connect(self.open_project)
        
        # --- View 2: The Workflow ---
        self.workflow_view = workflow_view
        self.workflow_view.back_to_dashboard.connect(self.close_project)
        
        self.stack.addWidget(self.list_view) # Index 0
        self.stack.addWidget(self.workflow_view)     # Index 1
        
        self.layout.addWidget(self.stack)
        self.setLayout(self.layout)
        self.list_view.request_documents()

    def open_project(self, doc,stage):
        print(f"Opening {doc}...")
        self.workflow_view.load_project(doc,stage)
        
        self.stack.setCurrentIndex(1) 

    def close_project(self):
        self.list_view.request_documents()
        self.stack.setCurrentIndex(0)
    
        

class WorkflowView(Page):
    back_to_dashboard = pyqtSignal()

    def __init__(self,parent):
        super().__init__(parent)
        self.current_document = None
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
        create_doc_page.next_stage.connect(self.next_stage)
        create_doc_page.new_document.connect(self.set_current_document)

        metadata_page = self.parent.MetadataPage()
        metadata_page.next_stage.connect(self.next_stage)

        review_page = self.parent.DocumentReviewPage()
        review_page.next_stage.connect(self.next_stage)

        self.stage_stack.addWidget(create_doc_page) # Index 0
        self.stage_stack.addWidget(metadata_page)    # Index 1    
        self.stage_stack.addWidget(review_page) # Index 2

    def load_project(self, doc,stage):
        if doc == None:
            self.lbl_project_title.setText('New Document')
            self.switch_stage(stage)
        else:
            self.lbl_project_title.setText(doc.doc_id)
            self.set_current_document(doc)
            self.switch_stage(stage) 
    
    def next_stage(self):
        self.switch_stage(self.stage_stack.currentIndex()+1)

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
        self.set_current_document(None)

    @pyqtSlot(Document)
    def set_current_document(self, doc):
        if doc != None:
            self.lbl_project_title.setText(doc.doc_id)
        self.current_document = doc
        for i in range(self.stage_stack.count()):
            page = self.stage_stack.widget(i)
            page.set_current_document(doc)

    @pyqtSlot(object)
    def db_update(self,doc):
        if self.current_document and doc.doc_id == self.current_document.doc_id:
            self.set_current_document(doc)

class ListView(Page):
    project_selected = pyqtSignal(object,int)
    db_request = pyqtSignal(dict,QObject)

    def __init__(self,parent):
        super().__init__(parent=parent)
        self.docs = []
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
        

    @pyqtSlot(Document,int)
    def card_clicked(self,doc,stage=1):
        if doc == None:
            print('Create New Document Clicked')
        else:
            print(f'{doc.doc_id} Card Clicked')
        self.project_selected.emit(doc,stage)

    @pyqtSlot(list)
    def show_documents(self):
        clear_layout(self.layout_flow)
        for document in self.docs:
            doc, stage = document
            card = DocumentCard(doc,stage)
            card.clicked.connect(self.card_clicked)
            self.layout_flow.addWidget(card)

    def load_documents(self,documents):
        self.docs = []
        for doc in documents.values():
            if doc.status['deskewed'] == False:
                self.docs.append((doc,0))
            elif doc.status['metadata'] == False:
                self.docs.append((doc,1))
            else:
                self.docs.append((doc,2))

    @pyqtSlot(dict)
    def request_documents(self):
        filter_data = {'needs_approval':False}
        ticket = JobTicket()
        ticket.data.connect(self.doc_return)
        ticket.error.connect(self.doc_error)
        self.db_request.emit(filter_data,ticket)

    @pyqtSlot(object,str)
    def doc_return(self,docs,job_id):
        self.load_documents(docs)
        self.show_documents()

    @pyqtSlot(str,str)
    def doc_error(self,error_msg,job_id):
        print(f'db_error: {error_msg}')
