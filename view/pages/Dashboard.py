from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QLabel,
    QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QObject
from PyQt6.QtGui import QCursor

from view.components import Page, CenteredFlowLayout, DocumentCard, NavigationBar
from model.data.document import Document
from model.logic.helpers import clear_layout
from model.service.signals import DatabaseTicket


class NewCard(QFrame):
    clicked = pyqtSignal(object, int)
    
    def __init__(self):
        super().__init__()
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # NEW: QSS Hook
        self.setObjectName("newCard")
        
        # Center the content
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # The Plus Icon
        icon_lbl = QLabel("+")
        icon_lbl.setObjectName("newCardIcon") # NEW: QSS Hook
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # The Text
        text_lbl = QLabel("New Document")
        text_lbl.setObjectName("newCardText") # NEW: QSS Hook
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl)
        
        self.setLayout(layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            print("Create New Document Emit")
            self.clicked.emit(None, 0)
        super().mousePressEvent(event)


class DashboardPage(Page):
    db_request = pyqtSignal(dict, object)
    
    def __init__(self, parent, list_view, workflow_view):
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

    def open_project(self, doc, stage):
        print(f"Opening {doc}...")
        self.workflow_view.load_project(doc, stage)
        self.stack.setCurrentIndex(1) 

    def close_project(self):
        self.list_view.request_documents()
        self.stack.setCurrentIndex(0)


class WorkflowView(Page):
    back_to_dashboard = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.current_document = None
        self._create_layout()

    def _create_layout(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # --- 1. Top Navigation Bar (The "Stepper") ---
        self.nav_bar = NavigationBar(self.return_to_dashboard,self)
        
        self.nav_bar.add_button('1. Files',0,lambda:self.switch_stage(0))
        self.nav_bar.add_button('2. Metadata',1,lambda:self.switch_stage(1))
        self.nav_bar.add_button('3. Review',2,lambda:self.switch_stage(2))
        
        layout.addWidget(self.nav_bar)
        
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

    def load_project(self, doc, stage):
        if doc == None:
            self.nav_bar.set_title('New Document')
            self.switch_stage(stage)
        else:
            self.nav_bar.set_title(doc.doc_id)
            self.set_current_document(doc)
            self.switch_stage(stage) 
    
    def next_stage(self):
        self.switch_stage(self.stage_stack.currentIndex()+1)

    def switch_stage(self, index,button=None):
        print(f'Switching to Stage{index}')
        self.stage_stack.setCurrentIndex(index)

        # Update Button States manually
        self.nav_bar.set_active(index)


    def return_to_dashboard(self):
        print('Return to Dashboard')
        self.back_to_dashboard.emit()
        self.set_current_document(None)

    @pyqtSlot(Document)
    def set_current_document(self, doc):
        if doc != None:
            self.nav_bar.page_title.setText(doc.doc_id)
        self.current_document = doc
        for i in range(self.stage_stack.count()):
            page = self.stage_stack.widget(i)
            page.set_current_document(doc)

    @pyqtSlot(object)
    def db_update(self, doc):
        if self.current_document and doc.doc_id == self.current_document.doc_id:
            self.set_current_document(doc)


class ListView(Page):
    project_selected = pyqtSignal(object, int)
    db_request = pyqtSignal(dict, QObject)

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.docs = []
        
        # Main Layout of the Page
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(40)
        
        # Header Section
        title = QLabel("Dashboard")
        title.setObjectName("pageTitle") # NEW: Global Typography Hook
        main_layout.addWidget(title)
        
        new_card = NewCard()
        new_card.clicked.connect(self.card_clicked)
        main_layout.addWidget(new_card)
        
        recent_documents_header = QLabel("Recent Documents")
        recent_documents_header.setObjectName("sectionTitle") # NEW: Global Typography Hook
        main_layout.addWidget(recent_documents_header)

        # --- The Scroll Area for the Grid ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setObjectName("transparentScrollArea") # NEW: QSS Hook

        # The container widget that holds the grid
        grid_container = QWidget()
        
        self.layout_flow = CenteredFlowLayout()  
        self.layout_flow.setSpacing(20)
        self.layout_flow.setContentsMargins(20, 20, 20, 20)
        
        grid_container.setLayout(self.layout_flow)
        scroll_area.setWidget(grid_container)
        
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
        
    # FIXED: Replaced 'Document' with 'object' to allow 'None' to pass without crashing
    @pyqtSlot(object, int)
    def card_clicked(self, doc, stage=1):
        if doc == None:
            print('Create New Document Clicked')
        else:
            print(f'{doc.doc_id} Card Clicked')
        self.project_selected.emit(doc, stage)

    @pyqtSlot(list)
    def show_documents(self):
        clear_layout(self.layout_flow)
        for document in self.docs:
            doc, stage = document
            card = DocumentCard(doc, stage)
            card.clicked.connect(self.card_clicked)
            card.delete_requested.connect(self.parent.process_manager.request_delete_doc)
            card.remove_requested.connect(self.parent.process_manager.request_remove_doc)
            self.layout_flow.addWidget(card)

    def load_documents(self, documents):
        self.docs = []
        for doc in documents.values():
            if doc.status['deskewed'] == False:
                self.docs.append((doc, 0))
            elif doc.status['metadata'] == False:
                self.docs.append((doc, 1))
            else:
                self.docs.append((doc, 2))

    @pyqtSlot(dict)
    def request_documents(self):
        filter_data = {'needs_approval': False}
        ticket = DatabaseTicket()
        ticket.data.connect(self.doc_return)
        ticket.error.connect(self.doc_error)
        self.db_request.emit(filter_data, ticket)

    @pyqtSlot(object, str)
    def doc_return(self, docs, job_id):
        self.load_documents(docs)
        self.show_documents()

    @pyqtSlot(str, str)
    def doc_error(self, error_msg, job_id):
        print(f'db_error: {error_msg}')