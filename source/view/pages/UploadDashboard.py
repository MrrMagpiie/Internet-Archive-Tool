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
from model.data.document import Document
from model.service.Signals import DatabaseTicket, JobTicket
from model.logic.helpers import clear_layout


class UploadDashboard(Page):
    project_selected = pyqtSignal(object, int)
    db_request = pyqtSignal(dict, QObject)

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.documents = {}
        self._create_layout()
    
    def _create_layout(self):
        # Main Layout of the Page
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(40)
        
        # Header Section
        self.title = QLabel("Upload Dashboard")
        self.title.setObjectName("pageTitle")
        main_layout.addWidget(self.title)
        self.nav_bar = NavigationBar(self.return_to_dashboard,self)
        self.nav_bar.setVisible(False)
        main_layout.addWidget(self.nav_bar)
        
        # Stacked Widget
        self.stack = QStackedWidget()
        self.stack.addWidget(self._main_page())   
        self.stack.addWidget(self._review_page()) 
        
        main_layout.addWidget(self.stack)
        self.setLayout(main_layout)

    def _main_page(self):
        dashboard = QWidget()
        dashboard_layout = QVBoxLayout()
        
        ready_documents_header = QLabel("Ready Documents")
        ready_documents_header.setObjectName("sectionTitle") 
        
        # --- The Scroll Area for the Grid ---
        ready_scroll_area = QScrollArea()
        ready_scroll_area.setWidgetResizable(True)
        ready_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        ready_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        ready_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        ready_scroll_area.setObjectName("transparentScrollArea")

        # The container widget that holds the grid
        ready_grid_container = QWidget()
        
        self.ready_flow = CenteredFlowLayout()  
        self.ready_flow.setSpacing(20)
        self.ready_flow.setContentsMargins(20, 20, 20, 20)
        
        ready_grid_container.setLayout(self.ready_flow)
        ready_scroll_area.setWidget(ready_grid_container)
        

        uploaded_documents_header = QLabel("Uploaded Documents")
        uploaded_documents_header.setObjectName("sectionTitle")
        
        # --- The Scroll Area for the Grid ---
        uploaded_scroll_area = QScrollArea()
        uploaded_scroll_area.setWidgetResizable(True)
        uploaded_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        uploaded_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        uploaded_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        uploaded_scroll_area.setObjectName("transparentScrollArea")
        
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
        self.review_page = self.parent.create_document_review_page()
        self.review_page.next_stage.connect(self.return_to_dashboard)
        self.review_page.approve_btn.setVisible(False)
        self.review_page.upload_btn.setVisible(True)
        return self.review_page

    @pyqtSlot(object, int)
    def card_clicked(self, doc, stage=1):
        print(f'{doc.doc_id} Card Clicked')
        self.review_page.set_current_document(doc)
        self.nav_bar.set_title(doc.doc_id)
        self.nav_bar.setVisible(True)
        self.title.setVisible(False)
        self.stack.setCurrentIndex(1)

    @pyqtSlot()
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
            card.delete_requested.connect(self.parent.process_manager.request_delete_doc)
            card.remove_requested.connect(self.parent.process_manager.request_remove_doc)
            if stage == 3:
                self.uploaded_flow.addWidget(card)
            else:   
                self.ready_flow.addWidget(card)

    def update_documents(self, doc):
        if doc.status.get('rejected') == True:
            return
        elif doc.status.get('uploaded') == True:
            self.documents[doc.doc_id] = (doc, 3)
        else:
            self.documents[doc.doc_id] = (doc, 2)

    def request_documents(self):
        filter_data = {
            'or_filters': {
                'needs_approval': True,
                'uploaded': True
            }
        }
        
        ticket = DatabaseTicket()
        ticket.data.connect(self.doc_return)
        ticket.error.connect(self.doc_error)
        
        self.db_request.emit(filter_data, ticket)

    @pyqtSlot(object, str)
    def doc_return(self, docs, job_id):
        self.documents.clear()
        for document in docs.values():
            self.update_documents(document)
        self.show_documents()

    @pyqtSlot(Exception, str)
    def doc_error(self, error, job_id):
        print(f'db_error: {error}')

    @pyqtSlot(Document)
    def document_update(self, doc):
        is_relevant = (
            doc.status.get('needs_approval',False),
            doc.status.get('uploaded', True),
            doc.doc_id in self.documents.keys()
        )
        if any(is_relevant):
            self.request_documents()