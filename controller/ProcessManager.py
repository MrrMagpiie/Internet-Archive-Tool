import json
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from uuid import uuid4

# Import Mixins
from .mixin.db_mixin import DatabaseMixin
from .mixin.doc_process_mixin import ProcessingMixin
from .mixin.upload_mixin import UploadMixin
from .mixin.image_mixin import ImageMixin

# Import Data Models
from model.data.document import Document
from model.data.schema import DocumentSchema
from config import RESOURCES_PATH

class ProcessManager(QObject, DatabaseMixin, ProcessingMixin, UploadMixin,ImageMixin):
    """
    Central Controller for the application.
    Uses Mixins to separate logic for Database, Processing, and Uploads.
    """
    # Global Signals
    busy_start = pyqtSignal()   # UI should show loading cursor
    busy_stop = pyqtSignal()    # UI should restore cursor

    task_started = pyqtSignal(str,str,str) # command, doc_id, task_id
    task_finished = pyqtSignal(str) # task_id


    db_update = pyqtSignal(Document) # Broadcasts DB changes to all views
    need_setup = pyqtSignal()        # Trigger Setup Wizard if config missing
    global_error = pyqtSignal(str) # Global error log, msg

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize the subsystems from Mixins
        self.setup_database()
        self.setup_processing()
        self.setup_upload()
        self.setup_image_loading()

    # --- Error Handling ---
    @pyqtSlot(str)
    def _handle_worker_error(self, error_msg):
        """Centralized error handler for all workers."""
        self.busy_stop.emit()
        print(f"{error_msg}")
        self.global_error.emit(error_msg)

    # --- Schema Logic (Lightweight, so kept in Main) ---
    @pyqtSlot(DocumentSchema)
    def save_schema(self, schema):
        schema_dict = schema.to_dict()
        schema_path = RESOURCES_PATH / 'document_schema.json'
        
        try:
            if schema_path.exists():
                with open(schema_path, 'r') as f: 
                    data = json.load(f)
            else:
                data = {}

            data[schema_dict.get('schema_name')] = schema_dict
            
            with open(schema_path, 'w') as f: 
                json.dump(data, f, indent=4)
                
        except Exception as e:
            self._handle_worker_error(f"Failed to save schema: {e}")

    # --- Cleanup ---
    def closeEvent(self, event=None):
        """Ensures all threads are killed properly on exit."""
        print("ProcessManager: Shutting down all workers...")
        self.shutdown_database()
        self.shutdown_processing()
        self.shutdown_upload()
        if event:
            event.accept()