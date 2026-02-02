import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget,QMainWindow, QGridLayout, 
    QSizePolicy, QSpacerItem,
)
from PyQt6.QtCore import pyqtSlot,pyqtSignal, QSize, QObject
from PyQt6.QtGui import QFont

#import pages 
from view.components import DocumentCard
from view.pages import *

class GUIManager(QObject):
    def __init__(self,manager):
        super().__init__()
        self.components = {}
        self.process_manager = manager
        
    def MainWindow(self):
        self.MainWindow = MainWindow(self)
        self.process_manager.discovery_complete.connect(self.MainWindow.on_discovery_complete)
        return self.MainWindow

    def DashboardPage(self,navigation_stack):
        dashboard_page = DashboardController(navigation_stack=navigation_stack,parent=self)
        return dashboard_page

    def DocumentReviewPage(self):
        review_page = DocumentReviewPage(self)
        review_page.document_reviewed.connect(self.process_manager.update_doc)
        self.process_manager.db_update.connect(review_page.db_update)
        review_page.upload.connect(self.process_manager.upload_document)
        return review_page

    def CreateDocumentPage(self):
        create_doc_page = CreateDocumentPage(self)
        self.process_manager.db_update.connect(create_doc_page.db_update)
        create_doc_page.discover_document.connect(self.process_manager.send_document_process_request)
        return create_doc_page

    def SettingsPage(self):
        settings_page = SettingsPage(self)
        return settings_page
    
    
    def MetadataPage(self):
        metadata_page = MetadataPage(self)
        return metadata_page

    def ReviewPage(self):
        review_page = ReviewPage(self)
        return review_page

    def HelpPage(self):
        help_page = HelpPage(self)
        return help_page

    @pyqtSlot()    
    def run_setup(self):
        '''
        nothing for now, will run the setup script
        '''
        pass
    