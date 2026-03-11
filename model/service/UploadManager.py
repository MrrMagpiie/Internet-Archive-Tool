from pathlib import Path
from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from model.data.document import Document
from model.logic.upload import uploadDocument, setup, get_unique_identifier,check_identifier_status

class UploadManager(QObject):
    """
    A QObject worker that runs the full document pipeline
    """
    success = pyqtSignal(object,str)
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
                command,signals, data = self.queue.get()
                if command == 'shutdown':
                    break 
                if signals.is_cancelled():
                            continue
                print(f'running {command}')
                

                try:
                    match command:
                        case 'upload':
                            doc = data
                            uploadDocument(doc,signals)
                            self.success.emit(doc,signals.job_id)
                        case 'setup':
                            email , password  = data
                            setup(email,password)
                            signals.data.emit(True,signals.job_id)
                        case 'unique_identifier':
                            identifier = data
                            signals.data.emit(get_unique_identifier(identifier),signals.job_id)
                        case 'identifier_status':
                            identifier = data
                            signals.data.emit(check_identifier_status(identifier),signals.job_id)
                        case _:
                            raise ValueError(f"Worker {self} received an unknown command: {command}")
                            
                except Exception as e:
                    err_msg = (f"Error processing command {command} for {signals.job_id}: {e}")
                    signals.error.emit(err_msg,signals.job_id)
                    self.error.emit(err_msg, signals.job_id)

        except Exception as e:
            self.error.emit(f"Upload Worker-level error: {e}",'')

