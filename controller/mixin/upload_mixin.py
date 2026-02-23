from PyQt6.QtCore import QThread, pyqtSlot
from queue import Queue
import os
from model.service.UploadManager import UploadManager
from config import user_config

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

        # Config Check
        if user_config.get('IA_CONFIG'):
            os.environ['IA_CONFIG_FILE'] = user_config.get('IA_CONFIG')
        else:
            self.need_setup.emit()

    @pyqtSlot(object)
    def request_upload(self, doc, ticket):
        self.task_started.emit('upload',doc.doc_id,ticket.job_id)
        self.upload_queue.put(('upload', (ticket, doc)))

    @pyqtSlot(object,str)
    def _handle_upload_success(self, doc,job_id):
        self.task_finished.emit(job_id)
        self.request_update_doc(doc)
        print(f'Upload Success: {doc.doc_id}')

    def shutdown_upload(self):
        self.upload_queue.put(('shutdown', None))
        self.upload_thread.quit()
        self.upload_thread.wait()