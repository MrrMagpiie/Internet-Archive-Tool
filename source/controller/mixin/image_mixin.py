from PyQt6.QtCore import QThread, pyqtSlot, QObject, QThreadPool
from pathlib import Path
from queue import Queue
from model.logic.load_image import ImageLoadTask


class ImageMixin:
    """Handles Image Processing & Discovery logic."""

    def setup_image_loading(self):
        self.image_cache = {}
        self.thread_pool = QThreadPool.globalInstance()
        self.thread_pool.setMaxThreadCount(4)

    @pyqtSlot(Path,QObject)
    def request_image(self,path,ticket):
        if path in self.image_cache:
            ticket.data.emit(self.image_cache[path],ticket.job_id)
            return
        self.image_cache[ticket.job_id] = path
        self.register_task('fetch_image',ticket,str(path))
        ticket.data.connect(self._handle_image_success)
        ticket.error.connect(self._handle_worker_error)
        task = ImageLoadTask(path, ticket)
        self.thread_pool.start(task)
        
    def clear_cache(self):
        self.image_cache.clear()

    def _cleanup_cache(self):
        """
        Garbage Collection: Deletes QImages from RAM if they are more 
        than 3 pages away from the user's current view.
        """
        keys_to_remove = []
        for indx in self.image_cache.keys():
            if abs(indx - self.current_image_index) > 3:
                keys_to_remove.append(indx)
                
        for indx in keys_to_remove:
            del self.image_cache[indx]

    def load_document(self,document:'Document'):
        for image_id, image in document.images.items():
            if image['processed']:
                image_cache[image_id] = image['processed']
            else:
                image_cache[image_id] = image['original']

    @pyqtSlot(object,str)
    def _handle_image_success(self,qimage,job_id):
        path = self.image_cache.pop(job_id)
        self.image_cache[path] = qimage
        self.task_finished.emit(job_id)

    def shutdown_image_loading(self):
        '''self.image_queue.put(('shutdown', None, None))
        self.image_thread.quit()
        self.image_thread.wait()'''