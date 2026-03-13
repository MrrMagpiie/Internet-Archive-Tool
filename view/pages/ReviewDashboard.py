import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QLabel, QPushButton, 
    QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QObject
from PyQt6.QtGui import QFont, QCursor

from view.components import (
    Page, CenteredFlowLayout, DocumentCard,
    SchemaForm,NavigationBar
)
from model.data import Document
from model.service.signals import DatabaseTicket, JobTicket
from model.logic.helpers import clear_layout


class ReviewPage(Page):
    project_selected = pyqtSignal(object, int)
    db_request = pyqtSignal(dict, QObject)

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.documents = {}
        self._create_layout()
        self.request_ready_documents()
        self.request_uploaded_documents()   
    
    def _create_layout(self):
        # Main Layout of the Page
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(40)
        
        # Header Section
        self.title = QLabel("Upload Dashboard")
        self.title.setObjectName("pageTitle") # REUSED: Global Typography Hook
        main_layout.addWidget(self.title)
        self.nav_bar = NavigationBar(self.return_to_dashboard,self)
        self.nav_bar.setVisible(False)
        main_layout.addWidget(self.nav_bar)
        
        # Stacked Widget
        self.stack = QStackedWidget()
        self.stack.addWidget(self._main_page())   # Index 0
        self.stack.addWidget(self._review_page()) # Index 1
        # FIXED: Removed the duplicate self.stack.addWidget(self.review_page) line
        
        main_layout.addWidget(self.stack)
        self.setLayout(main_layout)

    def _main_page(self):
        dashboard = QWidget()
        dashboard_layout = QVBoxLayout()
        
        ready_documents_header = QLabel("Ready Documents")
        ready_documents_header.setObjectName("sectionTitle") # REUSED Hook
        
        # --- The Scroll Area for the Grid ---
        ready_scroll_area = QScrollArea()
        ready_scroll_area.setWidgetResizable(True)
        ready_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        ready_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        ready_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        ready_scroll_area.setObjectName("transparentScrollArea") # REUSED Hook

        # The container widget that holds the grid
        ready_grid_container = QWidget()
        
        self.ready_flow = CenteredFlowLayout()  
        self.ready_flow.setSpacing(20)
        self.ready_flow.setContentsMargins(20, 20, 20, 20)
        
        ready_grid_container.setLayout(self.ready_flow)
        ready_scroll_area.setWidget(ready_grid_container)
        

        uploaded_documents_header = QLabel("Uploaded Documents")
        uploaded_documents_header.setObjectName("sectionTitle") # REUSED Hook
        
        # --- The Scroll Area for the Grid ---
        uploaded_scroll_area = QScrollArea()
        uploaded_scroll_area.setWidgetResizable(True)
        uploaded_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        uploaded_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        uploaded_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        uploaded_scroll_area.setObjectName("transparentScrollArea") # REUSED Hook
        
        # The container widget that holds the grid
        uploaded_grid_container = QWidget()
        
        self.uploaded_flow = CenteredFlowLayout()  
        self.uploaded_flow.setSpacing(20)
        self.uploaded_flow.setContentsMargins(20, 20, 20, 20)
        
        uploaded_grid_container.setLayout(self.uploaded_flow)
        uploaded_scroll_area.setWidget(uploaded_grid_container)
        
        dashboard_layout.addWidget(ready_documents_header)
        dashboard_layout.addWidget(ready_scroll_area)
        dashboard_layout.addWidget(uploaded_documents_header)
        dashboard_layout.addWidget(uploaded_scroll_area)
        dashboard.setLayout(dashboard_layout)
        
        return dashboard

    def _review_page(self):
        self.review_page = self.parent.DocumentReviewPage()
        self.review_page.approve_btn.setVisible(False)
        self.review_page.upload_btn.setVisible(True)
        return self.review_page

    @pyqtSlot(object, int)
    def card_clicked(self, doc, stage=1):
        print(f'{doc.doc_id} Card Clicked')
        self.review_page.set_current_document(doc)
        self.nav_bar.setVisible(True)
        self.title.setVisible(False)
        self.stack.setCurrentIndex(1)

    def return_to_dashboard(self):
        self.review_page.set_current_document(None)
        self.title.setVisible(True)
        self.nav_bar.setVisible(False)
        self.stack.setCurrentIndex(0)

    @pyqtSlot(list)
    def show_documents(self):
        clear_layout(self.ready_flow)
        clear_layout(self.uploaded_flow)

        for document in self.documents.values():
            doc, stage = document
            card = DocumentCard(doc, stage)
            card.clicked.connect(self.card_clicked)
            if stage == 3:
                self.uploaded_flow.addWidget(card)
            else:   
                self.ready_flow.addWidget(card)

    def update_documents(self, doc):
        if doc.status.get('metadata') == False:
            self.documents[doc.doc_id] = (doc, 1)
        elif doc.status.get('deskewed') == True:
            self.documents[doc.doc_id] =(doc, 2)
        elif doc.status.get('uploaded') == True:
            self.documents[doc.doc_id] = (doc, 3)
        elif doc.status.get('rejected') == True:
            # FIXED: Safe deletion to prevent KeyError
            self.documents.pop(doc.doc_id, None) 
        else:
            self.documents[doc.doc_id] = (doc, 0)

    @pyqtSlot(dict)
    def request_ready_documents(self):
        filter_data = {'needs_approval': True}
        ticket = DatabaseTicket()
        ticket.data.connect(self.doc_return)
        ticket.error.connect(self.doc_error)
        self.db_request.emit(filter_data, ticket)

    def request_uploaded_documents(self):
        filter_data = {'uploaded': True}
        ticket = DatabaseTicket()
        ticket.data.connect(self.doc_return)
        ticket.error.connect(self.doc_error)
        self.db_request.emit(filter_data, ticket)

    @pyqtSlot(object, str)
    def doc_return(self, docs, job_id):
        for document in docs.values():
            self.update_documents(document)
        self.show_documents()

    @pyqtSlot(str, str)
    def doc_error(self, error_msg, job_id):
        print(f'db_error: {error_msg}')

    @pyqtSlot(Document)
    def db_update(self, doc):
        is_relevant = (
            doc.status.get('needs_approval', False),
            doc.status.get('uploaded', False),
            doc.doc_id in self.documents.keys()
        )
        if any(is_relevant): 
            self.update_documents(doc)
            self.show_documents()