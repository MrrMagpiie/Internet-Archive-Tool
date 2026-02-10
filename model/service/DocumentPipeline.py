from pathlib import Path
from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from model.data.document import Document
from model.logic.discover import *
from model.logic.deskew import *
from model.logic.metadata import *

class DocPipelineRequest(QObject):
    data = pyqtSignal(Document)
    error = pyqtSignal(str)

class DocumentPipelineWorker(QObject):
    """
    A QObject worker that runs the full document pipeline
    """
    image_error = pyqtSignal(Exception) # exception
    doc_error = pyqtSignal(str,Exception) # doc_id and exception
    deskew_error = pyqtSignal(str, Exception)
    document = pyqtSignal(Document)
    error = pyqtSignal(str)

    def __init__(self,queue: Queue):
        super().__init__()
        self.queue = queue
        print('initpipe')

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
                    if command == 'discover':
                        signals, doc_data = data
                        in_dir, out_dir = doc_data
                        doc = self.discover(in_dir,out_dir)
                        if isinstance(doc,Document):
                            signals.data.emit(doc)
                            self.document.emit(doc)
                            
                    if command == 'metadata':
                        signals, doc_data = data
                        doc, metadata, metadata_type = doc_data
                        if isinstance(doc,Document):
                            doc = add_metadata_to_document(doc, metadata,metadata_type)
                            doc.status['metadata'] = True
                            signals.data.emit(doc)
                            self.document.emit(doc)

                    if command == 'deskew':
                        signals, doc = data
                        if isinstance(doc,Document):
                            self.deskew(doc)
                            doc.status['deskewed'] = True
                            signals.data.emit(doc)
                            self.document.emit(doc)

                except Exception as e:
                    signals.error.emit((f"Error processing command {command}: {e}"))

        except Exception as e:
            signals.error.emit(f"Worker-level error: {e}")
            self.error.emit(f"Worker-level error: {e}")

    def discover(self,in_dir,out_dir):
            image_list = discover_images(in_dir)

            try:
                documents_dict = images_to_documents(image_list)
            except Exception as e:
                self.error.emit(f'image to doc error: {e}')

            if len(documents_dict.keys()) == 1:
                for doc_id in documents_dict.keys():
                    try:
                        doc = create_document(doc_id,documents_dict[doc_id])
                        return doc
                    except Exception as e:
                        self.error.emit(f'doc creation error: {doc_id},{e}')
            else:
                print('more that one Doc in folder')
                return False
            
    def deskew(self,doc:Document):
        try:
            deskew_document(doc)
        except Exception as e:
            self.error.emit(f'{doc.doc_id},{e}')
    
