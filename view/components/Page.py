from PyQt6.QtWidgets import (
     QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy,
    QPushButton, QLabel,QSplitter,QListWidget, QStackedWidget,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt
from model.data.document import Document

class Page(QWidget):
    def __init__(self,parent):
        super().__init__()
        self.parent = parent

    @pyqtSlot(str,Document)
    def doc_return(self,command,doc):
        pass
    
    @pyqtSlot(str)
    def doc_error(self,error_msg):
        pass

    @pyqtSlot(Document)
    def db_update(self,doc):
        pass 