import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget,QMainWindow, QGridLayout, 
    QSizePolicy, QSpacerItem,
)
from PyQt6.QtCore import pyqtSlot,pyqtSignal, QSize, QObject, Qt
from PyQt6.QtGui import QFont

#import pages 
#rom view.components import DocumentCard
from view.pages import *
from view.components import ProcessManagerWidget, DocumentImagePanel

class GUIManager(QObject):
    def __init__(self,manager):
        super().__init__()
        self.components = {}
        self.process_manager = manager
        self.process_manager.busy_start.connect(self.start_loading_cursor)
        self.process_manager.busy_stop.connect(self.stop_loading_cursor)


    def MainWindow(self):
        self.MainWindow = MainWindow(self)
        return self.MainWindow

    # --- Pages

    def DashboardPage(self,navigation_stack):
        workflow_view = Dashboard.WorkflowView(self)
        list_view = Dashboard.ListView(self)
        list_view.db_request.connect(self.process_manager.request_docs_by_status)
        dashboard_page = DashboardPage(parent=self,workflow_view=workflow_view,list_view=list_view)
        self.process_manager.db_update.connect(workflow_view.db_update)
    
        return dashboard_page

    def DocumentReviewPage(self):
        review_page = DocumentReviewPage(self)
        review_page.document_reviewed.connect(self.process_manager.request_update_doc)
        self.process_manager.db_update.connect(review_page.db_update)
        review_page.upload.connect(self.process_manager.request_upload)
        return review_page

    def CreateDocumentPage(self):
        create_doc_page = CreateDocumentPage(self)
        self.process_manager.db_update.connect(create_doc_page.db_update)
        create_doc_page.discover_document.connect(self.process_manager.request_discovery)
        create_doc_page.deskew_document.connect(self.process_manager.request_deskew)
        create_doc_page.image_request.connect(self.process_manager.request_image)
        return create_doc_page

    def SettingsPage(self):
        settings_page = SettingsPage(self)
        return settings_page
     
    def MetadataPage(self):
        metadata_page = MetadataPage(self)
        metadata_page.save_metadata.connect(self.process_manager.request_save_metadata)
        return metadata_page

    def ReviewPage(self):
        review_page = ReviewPage(self)
        review_page.db_request.connect(self.process_manager.request_docs_by_status)
        self.process_manager.db_update.connect(review_page.db_update)
        return review_page

    def HelpPage(self):
        help_page = HelpPage(self)
        return help_page

    def SchemaEditPage(self):
        schema_page = SchemaEditPage(self)
        schema_page.new_schema.connect(self.process_manager.save_schema)
        schema_page.delete_schema.connect(self.process_manager.delete_schema)
        return schema_page

    # --- Components ---

    def ProcessManagerWidget(self):
        process_widget = ProcessManagerWidget()
        self.process_manager.task_started.connect(process_widget.add_task)
        self.process_manager.task_finished.connect(process_widget.remove_task)
        return process_widget

    def DocumentImagePanel(self):
        image_panel = DocumentImagePanel(self)
        image_panel.image_request.connect(self.process_manager.request_image)
        return image_panel

    # --- Slots ----

    @pyqtSlot()
    def start_loading_cursor(self):
        """Helper to set the wait cursor."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    
    @pyqtSlot()
    def stop_loading_cursor(self):
        """Helper to restore the default cursor."""
        QApplication.restoreOverrideCursor()

    @pyqtSlot()    
    def run_setup(self):
        '''
        nothing for now, will run the setup script
        '''
        pass
    