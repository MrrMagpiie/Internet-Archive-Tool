import qdarktheme
import darkdetect
import sys
from PyQt6.QtWidgets import QApplication, QDialog
from PyQt6.QtCore import pyqtSlot,QObject, Qt
from view.pages import *
from view.components import ProcessManagerWidget, DocumentImagePanel
from model.settings_manager import app_settings
from view.theme import *
from config import RESOURCES_PATH


class GUIManager(QObject):
    def __init__(self,manager):
        super().__init__()
        self.components = {}
        self.process_manager = manager
        self.process_manager.busy_start.connect(self.start_loading_cursor)
        self.process_manager.busy_stop.connect(self.stop_loading_cursor)
        self.main_window = None

    def create_main_window(self):
        self.main_window = MainWindow(self)
        return self.maine_window

    # --- Pages --- 
    
    def create_login_page(self):
        login_page = LoginPage()
        login_page.login_request.connect(self.process_manager.request_login)
        login_page.login_successful.connect(self.transition_to_app)
        return login_page

    def create_dashboard_page(self,navigation_stack):
        workflow_view = Dashboard.WorkflowView(self)
        list_view = Dashboard.ListView(self)
        list_view.db_request.connect(self.process_manager.request_docs_by_status)
        self.process_manager.document_update.connect(list_view.document_update)
        self.process_manager.document_delete.connect(list_view.request_documents)
        dashboard_page = DashboardPage(parent=self,workflow_view=workflow_view,list_view=list_view)
        self.process_manager.document_update.connect(workflow_view.document_update)
    
        return dashboard_page

    def create_document_review_page(self):
        review_page = DocumentReviewPage(self)
        review_page.document_reviewed.connect(self.process_manager.request_update_doc)
        self.process_manager.document_update.connect(review_page.document_update)
        review_page.upload.connect(self.process_manager.request_upload)
        review_page.identifier_status.connect(self.process_manager.request_identifier_status)
        review_page.unique_identifier.connect(self.process_manager.request_unique_identifier)
        review_page.save_metadata.connect(self.process_manager.request_update_doc)
        return review_page

    def create_discovery_page(self):
        discovery_page = SingleDiscoveryPage(self)
        discovery_page.image_request.connect(self.process_manager.request_image)
        discovery_page.discover_document.connect(self.process_manager.request_discovery)
        discovery_page.deskew_document.connect(self.process_manager.request_deskew)
        discovery_page.save_metadata.connect(self.process_manager.request_update_doc)
        return discovery_page

    def create_batch_discovery_page(self):
        discovery_page = BatchDiscoveryPage(self)
        discovery_page.batch_request.connect(self.process_manager.request_batch_discovery)
        discovery_page.discover_document.connect(self.process_manager.request_discovery)
        discovery_page.deskew_document.connect(self.process_manager.request_deskew)
        discovery_page.save_metadata.connect(self.process_manager.request_update_doc)
        return discovery_page

    def create_settings_page(self):
        settings_page = SettingsPage(self)
        return settings_page
     
    def create_metadata_page(self):
        metadata_page = MetadataPage(self)
        metadata_page.save_metadata.connect(self.process_manager.request_update_doc)
        return metadata_page

    def create_upload_dashboard(self):
        upload_page = UploadDashboard(self)
        upload_page.db_request.connect(self.process_manager.request_docs_by_status)
        upload_page.request_documents()
        self.process_manager.document_update.connect(upload_page.document_update)
        self.process_manager.document_delete.connect(upload_page.request_documents)
        return upload_page

    def create_help_page(self):
        help_page = HelpPage(self)
        return help_page

    def create_schema_edit_page(self):
        schema_page = SchemaEditPage(self)
        schema_page.new_schema.connect(self.process_manager.save_schema)
        schema_page.delete_schema.connect(self.process_manager.delete_schema)
        return schema_page

    def create_setup_wizard(self, need_setup):
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
        
        return wizard

    # --- Components ---

    def create_process_manager_widget(self):
        process_widget = ProcessManagerWidget()
        self.process_manager.task_started.connect(process_widget.add_task)
        self.process_manager.task_finished.connect(process_widget.remove_task)
        return process_widget

    def create_document_image_panel(self):
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
    def transition_to_app(self):
        if not self.main_window:
            self.main_window = MainWindow(self)
            self.main_window.show()

    @pyqtSlot(str)
    def setup_theme(self,theme_choice = None):
        """
        Resolves the theme choice, compiles the custom QSS, 
        and applies it to the application.
        """
        
        if not theme_choice: theme_choice = app_settings.get("THEME", "auto")

        # 1. Resolve "auto" to explicitly "dark" or "light"
        if theme_choice == "auto":
            # darkdetect returns 'Dark' or 'Light' based on the OS settings
            os_theme = darkdetect.theme()
            resolved_theme = os_theme.lower() if os_theme else "dark" # Fallback to dark
        else:
            resolved_theme = theme_choice

        # 2. Pick the correct dictionary
        palette = DARK_PALETTE if resolved_theme == "dark" else LIGHT_PALETTE
        
        # 3. Read your raw stylesheet
        with open(RESOURCES_PATH / "style.qss", "r") as f:
            raw_qss = f.read()
            
        # 4. Compile: Swap every {{variable}} with its hex code
        for var_name, hex_code in palette.items():
            raw_qss = raw_qss.replace(var_name, hex_code)
            
        # 5. Apply the fully compiled string to the application
        qdarktheme.setup_theme(
            theme=resolved_theme, 
            additional_qss=raw_qss
        )