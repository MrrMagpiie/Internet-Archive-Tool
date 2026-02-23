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
from model.service.signals import JobTicket
from model.data.document import Document
from model.logic.helpers import clear_layout



class ReviewPage(Page):
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
            if doc.status['metadata'] == False:
                self.docs.append((doc,1))
            elif doc.status['deskewed'] == True:
                self.docs.append((doc,2))
            else:
                self.docs.append((doc,0))

    @pyqtSlot(dict)
    def request_documents(self):
        filter_data = {'needs_approval':True}
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

    @pyqtSlot(Document)
    def db_update(self,doc):
        if doc.status['needs_approval'] == True:
            self.request_documents()

