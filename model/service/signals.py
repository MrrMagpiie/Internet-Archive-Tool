import uuid
import threading
from PyQt6.QtCore import QObject, pyqtSignal

class JobTicket(QObject):
    """
    Base class for all asynchronous background tasks.
    Acts as a self-contained envelope containing a unique ID and the callback signals.
    """

    data = pyqtSignal(object,str)# data return, job_id 
    error = pyqtSignal(Exception,str)# error msg, job_id
    progress = pyqtSignal(str, int, object) # job_id, value, step_text
    canceled = pyqtSignal(str) #job_id


    def __init__(self, job_id=None, parent=None):
        super().__init__(parent)
        self.job_id = job_id or str(uuid.uuid4())
        self._cancel_flag = threading.Event()

    def cancel(self):
        """Called by the UI to request cancellation."""
        self._cancel_flag.set()
        self.canceled.emit(self.job_id)

    def is_cancelled(self) -> bool:
        """Called by the Worker to check if it should stop."""
        return self._cancel_flag.is_set()

    def update_progress(self,value, step_text=None):
        self.progress.emit(self.job_id, value, step_text)

    def interceptor(self, base_progress, max_progress):
        self.interceptor = TqdmInterceptor(self, base_progress, max_progress)
        return self.interceptor

class DatabaseTicket(JobTicket):
    interupt = pyqtSignal()
    """
    Specialized ticket for database operations.
    """
    def cancel(self):
        self._cancel_flag.set()
        self.interupt.emit()


import sys
import re

class TqdmInterceptor:
    """Catches terminal output, extracts the percentage, and emits it to the GUI."""
    def __init__(self, ticket, base_progress, max_progress):
        self.ticket = ticket
        self.base_progress = base_progress
        self.max_progress = max_progress
        self.progress_range = max_progress - base_progress
        
        # Save a reference to the real terminal output so we don't break the console
        self.original_stderr = sys.stderr
        
    def write(self, text):
        # 1. Forward the text to the real terminal so you can still see it in the logs
        self.original_stderr.write(text)
        
        # 2. Look for the percentage number just before the '%' sign (e.g., "23%")
        match = re.search(r'(\d+)%', text)
        if match:
            file_pct = int(match.group(1))
            
            # 3. Scale the file's 0-100% into our UI's remaining 75-95% block
            overall_pct = self.base_progress + int((file_pct / 100) * self.progress_range)
            
            # 4. Emit the signal back to your PyQt window!
            self.ticket.update_progress(overall_pct, f"Uploading file... {file_pct}%")

    def flush(self):
        # tqdm calls flush() frequently, so we must pass it along to the real stderr
        self.original_stderr.flush()