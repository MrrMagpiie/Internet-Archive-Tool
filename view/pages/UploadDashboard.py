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
    SchemaForm
)
from model.data import Document
from model.service.signals import DatabaseTicket, JobTicket
from model.logic.helpers import clear_layout


class UploadDashboard(Page):
    project_selected = pyqtSignal(object, int)
    db_request = pyqtSignal(dict, QObject)

    def __init__(self,parent):
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
        title = QLabel("Upload Dashboard")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        
        nav_bar = QFrame()
        nav_bar.setFixedHeight(60)
        nav_bar.setStyleSheet("background-color: #f6f8fa; border-bottom: 1px solid #d1d5da;")
        nav_layout = QHBoxLayout()
        
        # "Back" Button
        self.btn_back = QPushButton("← All Projects")
        self.btn_back.setVisible(False)
        self.btn_back.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_back.setStyleSheet("border: none; color: #586069; font-weight: bold;")
        self.btn_back.clicked.connect(self.return_to_dashboard)

        nav_layout.addWidget(self.btn_back)
        nav_layout.addSpacing(20)
        nav_layout.addWidget(title)
        nav_layout.addStretch()

        nav_bar.setLayout(nav_layout)


        main_layout.addWidget(nav_bar)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._main_page())
        self.stack.addWidget(self._review_page())
        self.stack.addWidget(self.review_page)
        main_layout.addWidget(self.stack)

        self.setLayout(main_layout)

    def _main_page(self):
        dashboard = QWidget()
        dashboard_layout = QVBoxLayout()
        ready_documents_header = QLabel("Ready Documents")
        ready_documents_header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        

        # --- The Scroll Area for the Grid ---
        ready_scroll_area = QScrollArea()
        ready_scroll_area.setWidgetResizable(True)
        ready_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        ready_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        ready_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        ready_scroll_area.setStyleSheet("background-color: transparent;") # Let window bg show

       
        # The container widget that holds the grid
        ready_grid_container = QWidget()
        
        self.ready_flow = CenteredFlowLayout()  
        self.ready_flow.setSpacing(20)
        self.ready_flow.setContentsMargins(20, 20, 20, 20)
        
        ready_grid_container.setLayout(self.ready_flow)
        ready_scroll_area.setWidget(ready_grid_container)
        

        uploaded_documents_header = QLabel("Uploaded Documents")
        uploaded_documents_header.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        

        # --- The Scroll Area for the Grid ---
        uploaded_scroll_area = QScrollArea()
        uploaded_scroll_area.setWidgetResizable(True)
        uploaded_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        uploaded_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        uploaded_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        uploaded_scroll_area.setStyleSheet("background-color: transparent;") # Let window bg show

       
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

    @pyqtSlot(Document,int)
    def card_clicked(self,doc,stage=1):
        print(f'{doc.doc_id} Card Clicked')
        self.review_page.set_current_document(doc)
        self.btn_back.setVisible(True)
        self.stack.setCurrentIndex(1)

    def return_to_dashboard(self):
        self.review_page.set_current_document(None)
        self.btn_back.setVisible(False)
        self.stack.setCurrentIndex(0)

    @pyqtSlot(list)
    def show_documents(self):
        clear_layout(self.ready_flow)
        clear_layout(self.uploaded_flow)

        for document in self.documents.values():
            doc, stage = document
            card = DocumentCard(doc,stage)
            card.clicked.connect(self.card_clicked)
            if stage == 3:
                self.uploaded_flow.addWidget(card)
            else:   
                self.ready_flow.addWidget(card)

    def update_documents(self,doc):
        if doc.status['metadata'] == False:
            self.documents[doc.doc_id] = (doc,1)
        elif doc.status['deskewed'] == True:
            self.documents[doc.doc_id] =(doc,2)
        elif doc.status['uploaded'] == True:
            self.documents[doc.doc_id] = (doc,3)
        elif doc.status['rejected'] == True:
            del self.documents[doc.doc_id]
        else:
            self.documents[doc.doc_id] = (doc,0)

    @pyqtSlot(dict)
    def request_ready_documents(self):
        filter_data = {'needs_approval':True}
        ticket = DatabaseTicket()
        ticket.data.connect(self.doc_return)
        ticket.error.connect(self.doc_error)
        self.db_request.emit(filter_data,ticket)

    def request_uploaded_documents(self):
        filter_data = {'uploaded':True}
        ticket = DatabaseTicket()
        ticket.data.connect(self.doc_return)
        ticket.error.connect(self.doc_error)
        self.db_request.emit(filter_data,ticket)

    @pyqtSlot(object,str)
    def doc_return(self,docs,job_id):
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


