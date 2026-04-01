from PyQt6.QtCore import QThread, pyqtSlot
from queue import Queue
from pathlib import Path
import os
from model.service.UploadManager import UploadManager
from config import IA_CONFIG_PATH
from model.service.signals import JobTicket, DatabaseTicket


class UploadMixin:
    """Handles Internet Archive Upload logic."""

    def setup_upload(self):
        self.need_config = not IA_CONFIG_PATH.exists()
        self.upload_thread = QThread()
        self.upload_queue = Queue()
        self.upload_worker = UploadManager(self.upload_queue)
        self.upload_worker.success.connect(self._handle_upload_success)
        self.upload_worker.error.connect(self._handle_worker_error)

        self.upload_worker.moveToThread(self.upload_thread)
        self.upload_thread.started.connect(self.upload_worker.run)
        self.upload_thread.start()
        
        os.environ['IA_CONFIG_FILE'] =str(IA_CONFIG_PATH)

    @pyqtSlot(tuple,JobTicket)
    def ia_config(self,data,ticket:JobTicket):
        self.busy_start.emit()
        ticket.data.connect(lambda:self.busy_stop.emit())
        ticket.error.connect(lambda:self.busy_stop.emit())
        self.register_task('ia_config',ticket)
        self.upload_queue.put(('setup',ticket,data))
        
    @pyqtSlot(object,object)
    def request_upload(self, doc, ticket):
        self.register_task('upload',ticket,doc.doc_id)
        self.upload_queue.put(('upload', ticket, doc))
    
    @pyqtSlot(str,object)
    def request_identifier_status(self,identifier,ticket):
        self.register_task('identifier_status',ticket)
        self.upload_queue.put(('identifier_status',ticket,identifier))
    
    @pyqtSlot(str,object)
    def request_unique_identifier(self,identifier,ticket):
        self.register_task('unique_identifier',ticket)
        self.upload_queue.put(('unique_identifier',ticket,identifier))

    @pyqtSlot(object,str)
    def _handle_upload_success(self, doc,job_id):
        self.complete_task(job_id)
        ticket = DatabaseTicket()
        self.request_update_doc(doc,ticket)
        print(f'Upload Success: {doc.doc_id}')

    def shutdown_upload(self):
        self.upload_queue.put(('shutdown', None, None))
        self.upload_thread.quit()
        self.upload_thread.wait()