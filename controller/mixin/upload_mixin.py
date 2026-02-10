from PyQt6.QtCore import QThread, pyqtSlot
from queue import Queue
import os
from model.service.UploadManager import UploadManager, UploadRequest
from config import user_config

class UploadMixin:
    """Handles Internet Archive Upload logic."""

    def setup_upload(self):
        self.upload_thread = QThread()
        self.upload_queue = Queue()
        self.upload_worker = UploadManager(self.upload_queue)

        self.upload_worker.document.connect(self._handle_upload_success)
        self.upload_worker.error.connect(self._handle_worker_error)

        self.upload_worker.moveToThread(self.upload_thread)
        self.upload_thread.started.connect(self.upload_worker.run)
        self.upload_thread.start()

        # Config Check
        if user_config.get('IA_CONFIG'):
            os.environ['IA_CONFIG_FILE'] = user_config.get('IA_CONFIG')
        else:
            self.need_setup.emit()

    @pyqtSlot(object)
    def request_upload(self, doc, requester=None):
        signals = self._attach_signals(UploadRequest(), requester, {'data': 'upload_success', 'error': 'upload_error'})
        self.busy_start.emit()
        self.upload_queue.put(('upload', (signals, doc)))

    @pyqtSlot(object)
    def _handle_upload_success(self, doc):
        self.busy_stop.emit()
        self.request_update_doc(doc)
        print(f'Upload Success: {doc.doc_id}')

    def shutdown_upload(self):
        self.upload_queue.put(('shutdown', None))
        self.upload_thread.quit()
        self.upload_thread.wait()