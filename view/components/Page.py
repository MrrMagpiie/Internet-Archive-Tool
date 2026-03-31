from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSlot
from model.data.document import Document

class Page(QWidget):
    def __init__(self,parent):
        super().__init__()
        self.parent = parent

    @pyqtSlot(Document,str)
    def doc_return(self,doc,job_id):
        pass
    
    @pyqtSlot(str,str)
    def doc_error(self,error_msg,job_id):
        pass

    @pyqtSlot(Document)
    def document_update(self,doc):
        pass 