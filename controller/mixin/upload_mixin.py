from PyQt6.QtCore import QThread, pyqtSlot
from queue import Queue
from pathlib import Path
import os
from model.service.UploadManager import UploadManager
from config import IA_CONFIG

class UploadMixin:
    """Handles Internet Archive Upload logic."""

    def setup_upload(self):
        self.upload_thread = QThread()
        self.upload_queue = Queue()
        self.upload_worker = UploadManager(self.upload_queue)

        self.upload_worker.success.connect(self._handle_upload_success)
        self.upload_worker.error.connect(self._handle_worker_error)

        self.upload_worker.moveToThread(self.upload_thread)
        self.upload_thread.started.connect(self.upload_worker.run)
        self.upload_thread.start()

        os.environ['IA_CONFIG_FILE'] =str(IA_CONFIG)

    @pyqtSlot(object,object)
    def ia_config(self,ticket,data):
        self.busy_start.emit()
        ticket.data.connect(lambda:self.busy_stop.emit())
        ticket.error.connect(lambda:self.busy_stop.emit())
        self.upload_queue.put(('setup',ticket,data))
        
    @pyqtSlot(object,object)
    def request_upload(self, doc, ticket):
        self.task_started.emit('upload',doc.doc_id,ticket)
        self.upload_queue.put(('upload', ticket, doc))
    
    @pyqtSlot(str,object)
    def request_identifier_status(self,identifier,ticket):
        self.upload_queue.put(('identifier_status',ticket,identifier))
    
    @pyqtSlot(str,object)
    def request_unique_identifier(self,identifier,ticket):
        self.upload_queue.put(('unique_identifier',ticket,identifier))

    @pyqtSlot(object,str)
    def _handle_upload_success(self, doc,job_id):
        self.task_finished.emit(job_id)
        self.request_update_doc(doc)
        print(f'Upload Success: {doc.doc_id}')

    def shutdown_upload(self):
        self.upload_queue.put(('shutdown', None))
        self.upload_thread.quit()
        self.upload_thread.wait()