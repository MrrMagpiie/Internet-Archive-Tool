import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget,QMainWindow, QGridLayout, 
    QSizePolicy, QSpacerItem, QDialog
)
from PyQt6.QtCore import pyqtSlot,pyqtSignal, QSize, QObject, Qt
from PyQt6.QtGui import QFont
from view.pages import *
from view.components import ProcessManagerWidget, DocumentImagePanel

class GUIManager(QObject):
    def __init__(self,manager):
        super().__init__()
        self.components = {}
        self.process_manager = manager
        self.process_manager.busy_start.connect(self.start_loading_cursor)
        self.process_manager.busy_stop.connect(self.stop_loading_cursor)
        self.process_manager.need_setup.connect(self.run_setup)
        self.main_window = None


    def MainWindow(self):
        self.MainWindow = MainWindow(self)
        return self.MainWindow

    # --- Pages --- 
    
    def LoginPage(self):
        login_page = LoginPage()
        login_page.login_request.connect(self.process_manager.request_login)
        login_page.login_successful.connect(self.transition_to_app)
        return login_page


    def DashboardPage(self,navigation_stack):
        workflow_view = Dashboard.WorkflowView(self)
        list_view = Dashboard.ListView(self)
        list_view.db_request.connect(self.process_manager.request_docs_by_status)
        self.process_manager.document_update.connect(list_view.document_update)
        self.process_manager.document_delete.connect(list_view.request_documents)
        dashboard_page = DashboardPage(parent=self,workflow_view=workflow_view,list_view=list_view)
        self.process_manager.document_update.connect(workflow_view.document_update)
    
        return dashboard_page

    def DocumentReviewPage(self):
        review_page = DocumentReviewPage(self)
        review_page.document_reviewed.connect(self.process_manager.request_update_doc)
        self.process_manager.document_update.connect(review_page.document_update)
        review_page.upload.connect(self.process_manager.request_upload)
        review_page.identifier_status.connect(self.process_manager.request_identifier_status)
        review_page.unique_identifier.connect(self.process_manager.request_unique_identifier)
        review_page.save_metadata.connect(self.process_manager.request_update_doc)
        return review_page

    def CreateDocumentPage(self,batch = False):
        if batch:
            create_doc_page = BatchDocumentPage(self)
            create_doc_page.batch_request.connect(self.process_manager.request_batch_discovery)
        else:
            create_doc_page = SingleDocumentPage(self)
            create_doc_page.image_request.connect(self.process_manager.request_image)
        
        create_doc_page.discover_document.connect(self.process_manager.request_discovery)
        create_doc_page.deskew_document.connect(self.process_manager.request_deskew)
        create_doc_page.save_metadata.connect(self.process_manager.request_update_doc)
        return create_doc_page

    def SettingsPage(self):
        settings_page = SettingsPage(self)
        return settings_page
     
    def MetadataPage(self):
        metadata_page = MetadataPage(self)
        metadata_page.save_metadata.connect(self.process_manager.request_update_doc)
        return metadata_page

    def UploadDashboard(self):
        upload_page = UploadDashboard(self)
        upload_page.db_request.connect(self.process_manager.request_docs_by_status)
        upload_page.request_documents()
        self.process_manager.document_update.connect(upload_page.document_update)
        self.process_manager.document_delete.connect(upload_page.request_documents)
        return upload_page

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

    @pyqtSlot(tuple)    
    def run_setup(self, need_setup):
        
        if any(need_setup):
            wizard = SetupWizard()
            need_config, need_db = need_setup

            if need_config:
                ia_page = IAPage()
                ia_page.verify_ia_creds.connect(self.process_manager.ia_config)
                wizard.addPage(ia_page)
            
            if need_db:
                admin_page = AdminPage()
                admin_page.admin_setup_data.connect(self.process_manager.new_user)
                wizard.addPage(admin_page)
            
            result = wizard.exec() 
                
            if result == QDialog.DialogCode.Rejected:
                self.process_manager.closeEvent()
                sys.exit(1)

        self.login_page = self.LoginPage()
        self.login_page.login_successful.connect(self.transition_to_app)
        self.login_page.show()

    def transition_to_app(self):
        if not self.main_window:
            self.main_window = MainWindow(self)
            self.main_window.show()




    