from PyQt6.QtCore import QThread, pyqtSlot, QObject
from queue import Queue
from model.data.document import Document
from model.service.DocumentPipeline import DocumentPipelineWorker, DocPipelineRequest

class ProcessingMixin:
    """Handles Image Processing & Discovery logic."""

    def setup_processing(self):
        self.proc_thread = QThread()
        self.proc_queue = Queue()
        self.proc_worker = DocumentPipelineWorker(self.proc_queue)

        self.proc_worker.document.connect(self._handle_proc_success)
        self.proc_worker.error.connect(self._handle_worker_error)
        
        self.proc_worker.moveToThread(self.proc_thread)
        self.proc_thread.started.connect(self.proc_worker.run)
        self.proc_thread.start()

    @pyqtSlot(tuple, QObject)
    def request_discovery(self, data, requester):
        signals = self._attach_signals(DocPipelineRequest(), requester, {'data': 'doc_return', 'error': 'doc_error'})
        self.busy_start.emit()
        self.proc_queue.put(('discover', (signals, data)))

    @pyqtSlot(tuple, QObject)
    def request_deskew(self, data, requester):
        signals = self._attach_signals(DocPipelineRequest(), requester, {'data': 'doc_return', 'error': 'doc_error'})
        self.busy_start.emit()
        self.proc_queue.put(('deskew', (signals, data)))
    
    @pyqtSlot(tuple,QObject)
    def request_save_metadata(self,data,requester):
        signals = self._attach_signals(DocPipelineRequest(), requester, {'data': 'doc_return', 'error': 'doc_error'})
        self.busy_start.emit()
        self.proc_queue.put(('metadata', (signals, data)))

    @pyqtSlot(str,Document)
    def _handle_proc_success(self,command, doc):
        self.busy_stop.emit()
        self.request_update_doc(doc)
        print(f'Pipeline Success: {command} {doc.doc_id}')

    def shutdown_processing(self):
        self.proc_queue.put(('shutdown', None))
        self.proc_thread.quit()
        self.proc_thread.wait()