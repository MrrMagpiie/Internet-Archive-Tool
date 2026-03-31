from PyQt6.QtCore import QThread, pyqtSlot, QObject
from queue import Queue
from model.data.document import Document
from model.service.DocumentPipeline import DocumentPipelineWorker
from pathlib import Path
from model.service.signals import DatabaseTicket, JobTicket


class ProcessingMixin:
    """Handles Image Processing & Discovery logic."""

    def setup_processing(self):
        self.proc_thread = QThread()
        self.proc_queue = Queue()
        self.proc_worker = DocumentPipelineWorker(self.proc_queue)

        self.proc_worker.success.connect(self._handle_proc_success)
        self.proc_worker.error.connect(self._handle_worker_error)
        
        self.proc_worker.moveToThread(self.proc_thread)
        self.proc_thread.started.connect(self.proc_worker.run)
        self.proc_thread.start()

    @pyqtSlot(Path, QObject)
    def request_discovery(self, data, ticket):
        self.register_task('discover', ticket, str(data))
        self.proc_queue.put(('discover', ticket, data))

    @pyqtSlot(tuple, QObject)
    def request_deskew(self, data, ticket):
        self.register_task('deskew', ticket,data.doc_id)
        self.proc_queue.put(('deskew', ticket, data))
    
    @pyqtSlot(tuple,JobTicket)
    def request_save_metadata(self,data,ticket):
        self.register_task('metadata', ticket,data[0].doc_id)
        self.proc_queue.put(('metadata', ticket, data))

    @pyqtSlot(Document,str)
    def _handle_proc_success(self,doc,job_id):
        ticket = DatabaseTicket()
        if isinstance(doc, bool):
            return
        self.request_update_doc(doc,ticket)

    def shutdown_processing(self):
        self.proc_queue.put(('shutdown', None, None))
        self.proc_thread.quit()
        self.proc_thread.wait()