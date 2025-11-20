import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget,QMainWindow, QGridLayout, 
    QSizePolicy, QSpacerItem
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

    @pyqtSlot()
    def DashboardPage(self,navigation_stack):
        dashboard_page = DashboardPage(navigation_stack=navigation_stack,parent=self)
        return dashboard_page

    @pyqtSlot()
    def SingleDocumentPage(self):
        single_doc = SingleDocumentPage(self)
        return single_doc

    def StepDashboardPage(self):
        step_dash = StepDashboardPage(self)
        return step_dash

    @pyqtSlot()
    def DiscoveryPage(self):
        discovery_page = DiscoveryPage(self)
    #    discovery_page.discovery_signal.connect(self.process_manager.start_discovery_pipeline)
        return discovery_page

    @pyqtSlot()
    def UploadPage(self):
        upload_page = UploadPage(self)
    #    self.process_manager.db_change.connect(upload_page.load_documents)
    #    upload_page.upload.connect(self.process_manager.start_upload_pipeline)
        return upload_page
    
    @pyqtSlot()
    def ApprovalPage(self):
        approval_page = ApprovalPage(self)
    #    approval_page.document_reviewed.connect(self.process_manager.db_doc_status)
    #    self.process_manager.db_change.connect(approval_page.load_documents)
        return approval_page
    
    @pyqtSlot()
    def MetadataPage(self):
        metadata_page = MetadataPage(self)
    #    self.process_manager.db_change.connect(metadata_page.load_documents)
    #    self.process_manager.schema_saved.connect(metadata_page._load_metadata_formats)
    #    metadata_page.db_metadata.connect(self.process_manager.db_metadata)
        return metadata_page

    @pyqtSlot()
    def DeskewPage(self):
        deskew_page = DeskewPage(self)
    #    deskew_page.deskew_signal.connect(self.process_manager.start_deskew_pipeline)
        return deskew_page
        
    '''
    @pyqtSlot()
    def CredentialsPage(self):
        credentials_page = CredentialsPage(self)
        credentials_page.setup.connect(self.process_manager.setup_ia_pipeline)
        self.process_manager.ia_setup_success.connect(self.credentials_page._setup_return)
        return credentials_page
    
    
    
    @pyqtSlot(bool) #edit
    def SchemaBuilderPage(self,edit=False):
        schema_builder_page = SchemaBuilderPage(parent=self,edit=edit)
        schema_builder_page.load_schema.connect(self.process_manager.load_schema)
        schema_builder_page.save_schema.connect(self.process_manager.save_schema)
        self.process_manager.schema_loaded.connect(schema_builder_page.displaySchema)
        self.process_manager.schema_saved.connect(schema_builder_page.saveResponse)
        schema_builder_page._create_layout()
        return schema_builder_page
    


    @pyqtSlot()
    def BatchPage(self):
        batch_page = BatchPage(self)
        batch_page.discovery_signal.connect(self.process_manager.start_discovery_pipeline)
        return batch_page'''
