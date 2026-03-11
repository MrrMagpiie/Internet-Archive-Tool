import json
import sys
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QDialog
from uuid import uuid4

# Import Mixins
from controller.mixin import *

# Import Data Models
from model.data.document import Document
from model.data.schema import DocumentSchema
from config import IA_CONFIG_PATH
from view.pages.SetupGui import FirstRunSetupDialog

class ProcessManager(QObject, DatabaseMixin, ProcessingMixin, UploadMixin, ImageMixin, SchemaMixin):
    """
    Central Controller for the application.
    Uses Mixins to separate logic for Database, Processing, and Uploads.
    """
    # Global Signals
    busy_start = pyqtSignal()   # UI should show loading cursor
    busy_stop = pyqtSignal()    # UI should restore cursor

    task_started = pyqtSignal(str,str,object) # command, doc_id, ticket
    task_finished = pyqtSignal(str) # job_id

    db_update = pyqtSignal(Document) # Broadcasts DB changes to all views
    need_setup = pyqtSignal(bool)        # Trigger Setup Wizard if config missing
    global_error = pyqtSignal(str) # Global error log, msg

    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize the subsystems from Mixins
        self.setup_database()
        self.setup_processing()
        self.setup_upload()
        self.setup_image_loading()



    def check_setup(self):
        if not IA_CONFIG_PATH.exists():
            self.need_setup.emit(True)
        else:
            self.need_setup.emit(False)


    # --- Error Handling ---
    @pyqtSlot(str)
    def _handle_worker_error(self, error_msg):
        """Centralized error handler for all workers."""
        self.busy_stop.emit()
        print(f"{error_msg}")
        self.global_error.emit(error_msg)

    # --- Cleanup ---
    def closeEvent(self, event=None):
        """Ensures all threads are killed properly on exit."""
        print("ProcessManager: Shutting down all workers...")
        self.shutdown_database()
        self.shutdown_processing()
        self.shutdown_upload()
        self.shutdown_image_loading()
        if event:
            event.accept()