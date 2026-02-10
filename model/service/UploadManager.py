from pathlib import Path
from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from model.data.document import Document
from model.logic.upload import uploadDocument, setup

class UploadRequest(QObject):
    data = pyqtSignal(Document)
    error = pyqtSignal(str)

class UploadManager(QObject):
    """
    A QObject worker that runs the full document pipeline
    """
    document = pyqtSignal(Document)
    error = pyqtSignal(str)

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

                    if command == 'setup':
                        signals, setup_data = data
                        email , password = setup_data
                        setup(email,password)
                            
                except Exception as e:
                    signals.error.emit((f"Error processing command {command}: {e}"))

        except Exception as e:
            signals.error.emit(f"Worker-level error: {e}")
            self.error.emit(f"Worker-level error: {e}")

