from PyQt6.QtCore import QThread, pyqtSlot, QObject, QThreadPool
from pathlib import Path
from queue import Queue
from model.logic.load_image import ImageLoadTask
from model.data.document import Document


class ImageMixin:
    """Handles Image Processing & Discovery logic."""

    def setup_image_loading(self):
        self.image_cache = {}
        self._pending_images = {}
        self.thread_pool = QThreadPool.globalInstance()
        self.thread_pool.setMaxThreadCount(4)

    @pyqtSlot(Path,QObject)
    def request_image(self,path,ticket):
        if path in self.image_cache:
            ticket.data.emit(self.image_cache[path],ticket.job_id)
            return
            
        self._pending_images[ticket.job_id] = path
        self.register_task('fetch_image',ticket,str(path))
        ticket.data.connect(self._handle_image_success)
        ticket.error.connect(self._handle_worker_error)
        
        task = ImageLoadTask(path, ticket)
        self.thread_pool.start(task)
        
    def clear_cache(self):
        self.image_cache.clear()
        self._pending_images.clear()

    def _cleanup_cache(self):
        """
        Garbage Collection: Keeps only the 10 most recently loaded images in memory.
        """
        if len(self.image_cache) > 10:
            keys = list(self.image_cache.keys())
            for k in keys[:-10]:
                del self.image_cache[k]

    def load_document(self,document:'Document'):
        self.clear_cache()
        for image_id, image in document.images.items():
            if image['processed']:
                image_cache[image_id] = image['processed']
            else:
                image_cache[image_id] = image['original']

    @pyqtSlot(object,str)
    def _handle_image_success(self,qimage,job_id):
        if job_id in self._pending_images:
            path = self._pending_images.pop(job_id)
            self.image_cache[path] = qimage
            self._cleanup_cache()
        self.task_finished.emit(job_id)

    def shutdown_image_loading(self):
        self.thread_pool.clear()