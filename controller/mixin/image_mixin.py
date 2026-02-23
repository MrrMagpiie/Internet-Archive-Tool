from PyQt6.QtCore import QThread, pyqtSlot, QObject
from pathlib import Path
from queue import Queue
from model.service.ImageLoader import ImageLoader,FetchImageRequest

class ImageMixin:
    """Handles Image Processing & Discovery logic."""

    def setup_image_loading(self):
        self.image_thread = QThread()
        self.image_queue = Queue()
        self.image_worker = ImageLoader(self.image_queue)

        self.image_worker.success.connect(self._handle_image_success)
        self.image_worker.error.connect(self._handle_worker_error)
        
        self.image_worker.moveToThread(self.image_thread)
        self.image_thread.started.connect(self.image_worker.run)
        self.image_thread.start()

    @pyqtSlot(Path,QObject)
    def request_image(self,data,ticket):
        self.task_started.emit('fetch image',str(data),ticket.job_id)
        self.image_queue.put(('single',(ticket,data)))
    
    def request_image_series(self,data,ticket):
        self.image_queue.put(('series',(ticket,data)))

    @pyqtSlot()
    def clear_queue(self):
        with self.image_queue.mutex:
            self.image_queue.queue.clear()

    @pyqtSlot(str)
    def _handle_image_success(self,job_id):
        self.task_finished.emit(job_id)
        print('image loaded')