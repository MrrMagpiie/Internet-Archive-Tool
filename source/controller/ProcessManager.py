import json
import sys
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QDialog


# Import Mixins
from controller.mixin import *

# Import Data Models
from model.data.document import Document
from model.data.schema import DocumentSchema
from config import IA_CONFIG_PATH, DB_PATH
from model.service.Signals import JobTicket, DatabaseTicket

class ProcessManager(QObject, DatabaseMixin, ProcessingMixin, UploadMixin, ImageMixin, SchemaMixin):
    """
    Central Controller for the application.
    Uses Mixins to separate logic for Database, Processing, and Uploads.
    """
    # Global Signals
    busy_start = pyqtSignal()   # UI show loading cursor
    busy_stop = pyqtSignal()    # UI restore cursor

    task_started = pyqtSignal(str,str,object) # command, text, ticket
    task_finished = pyqtSignal(str) # job_id
    queue_empty = pyqtSignal() # Queue is empty

    document_update = pyqtSignal(Document) # Broadcasts Document changes to all views
    document_delete = pyqtSignal(str) # Broadcasts Document deletion to all views

    need_setup = pyqtSignal(tuple)# Trigger Setup Wizard if config or db missing
    global_error = pyqtSignal(str) # Global error log, msg

    def __init__(self, parent=None):
        super().__init__(parent)
        # Initialize the subsystems from Mixins
        self.setup_database()
        self.setup_processing()
        self.setup_upload()
        self.setup_image_loading()
        self._active_tasks = {}

    def check_setup(self):
        check = (self.need_config, self.need_db)
        self.need_setup.emit(check)

    # --- Task Managment ---
    def register_task(self, command: str,ticket: JobTicket,text=None):
        ticket.data.connect(lambda: self.complete_task(ticket.job_id))
        ticket.canceled.connect(lambda: self.complete_task(ticket.job_id))

        self._active_tasks[ticket.job_id] = (command,ticket)
        if text:
            self.task_started.emit(command, text, ticket)

    def complete_task(self, job_id: str):
        if job_id not in self._active_tasks:
            return
        self._active_tasks.pop(job_id)
        self.task_finished.emit(job_id)

        if len(self._active_tasks) == 0:
            self.queue_empty.emit()

    def has_active_tasks(self) -> bool:
        print(f"Active Tasks: {self._active_tasks}")
        return len(self._active_tasks) > 0

    # --- Error Handling ---
    @pyqtSlot(Exception,str)
    def _handle_worker_error(self, error,job_id):
        """Centralized error handler for all workers."""
        self.complete_task(job_id)
        print(error)
        
    # --- Cleanup ---
    def closeEvent(self, event=None):
        """Ensures all threads are killed properly on exit."""
        
        print('ProcessManager: Canceling all tickets')
        active_tasks = list(self._active_tasks.values())
        for command, ticket in active_tasks:
            ticket.cancel()

        print("ProcessManager: Shutting down all workers...")
        self.shutdown_database()
        self.shutdown_processing()
        self.shutdown_upload()
        self.shutdown_image_loading()
        if event:
            event.accept()

