from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QLabel,
    QFrame, QScrollArea,QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QObject
from PyQt6.QtGui import QCursor

from view.components import Page, CenteredFlowLayout, DocumentCard, NavigationBar, ActionCard
from model.data import Document
from model.logic.helpers import clear_layout
from model.service import DatabaseTicket


class DashboardPage(Page):
    db_request = pyqtSignal(dict, object)
    
    def __init__(self, parent, list_view, workflow_view):
        super().__init__(parent=parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        # --- View 1: The Grid (Existing ListView) ---
        self.list_view = list_view
        self.list_view.project_selected.connect(self.open_project)
        self.list_view.new_batch.connect(self.new_batch)
        
        # --- View 2: The Workflow ---
        self.workflow_view = workflow_view
        self.workflow_view.back_to_dashboard.connect(self.close_project)
        
        self.stack.addWidget(self.list_view)
        self.stack.addWidget(self.workflow_view)
        
        self.list_view.request_documents()

    def open_project(self, doc, stage):
        print(f"Opening {doc}...")
        self.workflow_view.load_project(doc, stage)
        self.stack.setCurrentIndex(1)

    def new_batch(self):
        self.workflow_view.new_batch()
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
        self.nav_bar = NavigationBar(self.return_to_dashboard,self)
        layout.addWidget(self.nav_bar)
        
        # --- 2. The Internal Stack (The Stages) ---
        self.stage_stack = QStackedWidget()
        layout.addWidget(self.stage_stack)
        
        self.setLayout(layout)
        
        # Default to Scan
        self.switch_stage(0)
    
    def _create_batch_page(self):
        self.clear_stack()
        self.nav_bar.add_button('1. Files',0,lambda:self.switch_stage(0))
        discovery_page = self.parent.create_batch_discovery_page()
        discovery_page.next_stage.connect(self.return_to_dashboard)
        self.stage_stack.addWidget(discovery_page)


    def _create_pages(self):
        self.clear_stack()
        discovery_page = self.parent.create_discovery_page()
        discovery_page.new_document.connect(self.set_current_document)
        discovery_page.next_stage.connect(self.next_stage)
        
        metadata_page = self.parent.create_metadata_page()
        metadata_page.next_stage.connect(self.next_stage)

        review_page = self.parent.create_document_review_page()
        review_page.next_stage.connect(self.return_to_dashboard)
        
        self.nav_bar.add_button('1. Files',0,lambda:self.switch_stage(0))
        self.stage_stack.addWidget(discovery_page)
        self.stage_stack.addWidget(metadata_page)
        self.nav_bar.add_button('2. Metadata',1,lambda:self.switch_stage(1))
        self.stage_stack.addWidget(review_page)
        self.nav_bar.add_button('3. Review',2,lambda:self.switch_stage(2))
            
    def clear_stack(self):
        while self.stage_stack.count() > 0:
            page = self.stage_stack.widget(0)
            self.stage_stack.removeWidget(page)
            page.deleteLater()
        for button in self.nav_bar.button_group.buttons():
            self.nav_bar.button_group.removeButton(button)
            button.setParent(None)
            button.deleteLater()

    def new_batch(self):
        self._create_batch_page()

        self.nav_bar.set_title('New Batch')
        self.switch_stage(0)

    def load_project(self, doc, stage):
        self._create_pages()

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
        self.stage_stack.setCurrentIndex(index)
        self.nav_bar.set_active(index)

    def return_to_dashboard(self):
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

    @pyqtSlot(Document)
    def document_update(self, doc):
        if self.current_document and doc.doc_id == self.current_document.doc_id:
            self.set_current_document(doc)
            
class ListView(Page):
    project_selected = pyqtSignal(object, int)
    new_batch = pyqtSignal()
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
        title.setObjectName("pageTitle")
        main_layout.addWidget(title)
        
        action_card_layout = QHBoxLayout()
        new_card = ActionCard(icon='+',text='New Document')
        new_card.clicked.connect(lambda: self.project_selected.emit(None, 0))
        action_card_layout.addWidget(new_card)

        batch_card = ActionCard(icon='+',text='Batch Process')
        batch_card.clicked.connect(self.new_batch.emit)
        action_card_layout.addWidget(batch_card)
        main_layout.addLayout(action_card_layout) 
        
        recent_documents_header = QLabel("Recent Documents")
        recent_documents_header.setObjectName("sectionTitle")
        main_layout.addWidget(recent_documents_header)

        # --- The Scroll Area for the Grid ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setObjectName("transparentScrollArea") 

        # The container widget that holds the grid
        grid_container = QWidget()
        
        self.layout_flow = CenteredFlowLayout()  
        self.layout_flow.setSpacing(20)
        self.layout_flow.setContentsMargins(20, 20, 20, 20)
        
        grid_container.setLayout(self.layout_flow)
        scroll_area.setWidget(grid_container)
        
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    @pyqtSlot(list)
    def show_documents(self):
        clear_layout(self.layout_flow)
        for document in self.docs:
            doc, stage = document
            card = DocumentCard(doc, stage)
            card.clicked.connect(self.project_selected.emit)
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

    @pyqtSlot(str)
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

    @pyqtSlot(Exception, str)
    def doc_error(self, error, job_id):
        print(f'db_error: {error}')

    @pyqtSlot(Document)
    def document_update(self,doc):
        is_relevant = (
            not doc.status.get('needs_approval',False)
        )
        if is_relevant:
            self.request_documents()
