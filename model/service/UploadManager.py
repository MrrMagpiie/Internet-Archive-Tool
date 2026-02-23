from pathlib import Path
from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from model.data.document import Document
from model.logic.upload import uploadDocument, setup


class UploadManager(QObject):
    """
    A QObject worker that runs the full document pipeline
    """
    success = pyqtSignal(Document,str)
    error = pyqtSignal(str,str)

    def __init__(self,queue: Queue):
        super().__init__()
        self.queue = queue
        print('init upload')

    @pyqtSlot()
    def run(self):
        """The main worker loop. This runs in the QThread."""
        try:
            signals = None
            while True:
                command, data = self.queue.get()
                print(f'running {command}')
                if command == 'shutdown':
                    break 

                try:
                    if command == 'upload':
                        signals, doc = data
                        uploadDocument(doc)
                        self.success.emit(doc,signals.job_id)

                    if command == 'setup':
                        signals, setup_data = data
                        email , password = setup_data
                        setup(email,password)
                        self.success.emit(doc,signals.job_id)
                            
                except Exception as e:
                    err_msg = (f"Error processing command {command} for {signals.job_id}: {e}")
                    signals.error.emit(err_msg,signals.job_id)
                    self.error.emit(err_msg, signals.job_id)

        except Exception as e:
            self.error.emit(f"Upload Worker-level error: {e}",'')

