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

        self.image_worker.image.connect(self._handle_image_success)
        self.image_worker.error.connect(self._handle_worker_error)
        
        self.image_worker.moveToThread(self.image_thread)
        self.image_thread.started.connect(self.image_worker.run)
        self.image_thread.start()

    @pyqtSlot(Path,QObject)
    def request_image(self,data,requester):
        signals = self._attach_signals(FetchImageRequest(), requester, {'data': 'image_return', 'error': 'image_error'})
        
        self.image_queue.put(('single',(signals,data)))
    
    def request_image_series(self,data,requester):
        signals = self._attach_signals(FetchImageRequest(), requester, {'data': 'image_return', 'error': 'image_error'})
        self.image_queue.put(('series',(signals,data)))

    @pyqtSlot(object)
    def _handle_image_success(self,image):
        print('image loaded')