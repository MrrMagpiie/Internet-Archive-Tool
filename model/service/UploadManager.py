from pathlib import Path
from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from model.exceptions import MetadataError, PdfGenerationError, TaskCancelledError
from model.data import Document
class UploadManager(QObject):
    """
    A QObject worker that runs the full document pipeline
    """
    success = pyqtSignal(object,str)
    error = pyqtSignal(Exception,str)

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
                    signals.error.emit(e,signals.job_id)
                    self.error.emit(e, signals.job_id)

        except Exception as e:
            self.error.emit(e,'')
