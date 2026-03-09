import uuid
import threading
from PyQt6.QtCore import QObject, pyqtSignal

class JobTicket(QObject):
    """
    Base class for all asynchronous background tasks.
    Acts as a self-contained envelope containing a unique ID and the callback signals.
    """

    data = pyqtSignal(object,str)# data return, job_id 
    error = pyqtSignal(str,str)# error msg, job_id

    def __init__(self, job_id=None, parent=None):
        super().__init__(parent)
        self.job_id = job_id or str(uuid.uuid4())
        self._cancel_flag = threading.Event()

    def cancel(self):
        """Called by the UI to request cancellation."""
        self._cancel_flag.set()

    def is_cancelled(self) -> bool:
        """Called by the Worker to check if it should stop."""
        return self._cancel_flag.is_set()


class DocPipelineRequest(JobTicket):
    """Used for Discovery and Deskewing tasks."""
    pass

class DatabaseSignal(JobTicket):
    """Used for saving and loading documents from SQLite."""
    pass

class UploadRequest(JobTicket):
    """Used for Internet Archive upload tasks."""
    pass

class ImageLoadRequest(JobTicket):
    """Used by the UI to request high-res image loading."""
    pass