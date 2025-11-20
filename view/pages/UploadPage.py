
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget
)
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from view.components import Page

class UploadPage(Page):
    upload = pyqtSignal(str, QObject) #self
    
    def __init__(self, parent):
        super().__init__(parent)
        self.db_data = {}
        self.doc_list = []
        
        self.create_layout()

    def create_layout(self):
        main_layout = QHBoxLayout(self)
        self.upload_page = self.create_upload_page()
        main_layout.addWidget(self.upload_page)
       
    
    def create_upload_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Documents ready to Upload:"))
        self.doc_list = QListWidget()
        layout.addWidget(self.doc_list)
        upload_btn = QPushButton('Upload (does nothing atm)')
        upload_btn.clicked.connect(self._upload_document)
        layout.addWidget(upload_btn)
        
        return page
    
    @pyqtSlot(dict)
    def load_documents(self, db_data):
        """Receives the full manifest from the ProcessManager and populates the list."""
        self.doc_list.clear()
        self.db_data = db_data
        for doc_id, doc in db_data.items():
            if doc.status.get('approved', True):
                self.doc_list.addItem(doc_id)

    def _upload_document(self):
        self.upload.emit(self.doc_list.currentItem().text(),self)
