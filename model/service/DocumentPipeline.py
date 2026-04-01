from sqlite3 import OperationalError
from pathlib import Path
from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from model.data.document import Document
from model.logic.discover import *
from model.logic.deskew import *
from model.logic.metadata import *
from model.exceptions import DeskewError, ImageDiscoveryError, DocumentCreationError, DocumentDeletionError, TaskCancelledError
class DocumentPipelineWorker(QObject):
    """
    A QObject worker that runs the full document pipeline
    """
    success = pyqtSignal(object,str) # job_id
    error = pyqtSignal(Exception,str) # error_msg job_id 
    prog = pyqtSignal(int)# Progress Update

    def __init__(self,queue: Queue):
        super().__init__()
        self.queue = queue
        print('init DocumentPipelineWorker')
        

    @pyqtSlot()
    def run(self):
        """The main worker loop. This runs in the QThread."""
        try:
            print('Document Pipeline queue running')
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
                        case 'discover':
                            in_dir = data
                            doc = self.single_discover(in_dir)
                            if isinstance(doc,Document) and  not signals.is_cancelled():
                                signals.data.emit(doc,signals.job_id)
                                self.success.emit(doc,signals.job_id)
                            
                        case 'metadata':
                            doc, metadata, metadata_type = data
                            if isinstance(doc,Document):
                                doc = update_metadata_file(doc)
                                doc.status['metadata'] = True
                            if not signals.is_cancelled():
                                signals.data.emit(doc,signals.job_id)
                                self.success.emit(doc,signals.job_id)

                        case 'deskew':
                            doc = data
                            if isinstance(doc,Document):
                                self.deskew(doc,ticket=signals)
                                doc.status['deskewed'] = True
                            if not signals.is_cancelled():
                                signals.data.emit(doc,signals.job_id)
                                self.success.emit(doc,signals.job_id)

                except Exception as e:
                    signals.error.emit(e,signals.job_id)
                    self.error.emit(e,signals.job_id)

        except Exception as e:
            self.error.emit(e,'')
            traceback.print_exc()

    def single_discover(self,in_dir):
            image_list = discover_images(in_dir)

            try:
                documents_dict = images_to_documents(image_list)
            except Exception as e:
                raise ImageDiscoveryError() from e

            if len(documents_dict.keys()) == 1:
                for doc_id in documents_dict.keys():
                    try:
                        doc = create_document(doc_id,documents_dict[doc_id])
                        return doc
                    except Exception as e:
                        raise DocumentCreationError(doc_id)
            else:
                raise ImageDiscoveryError('Directory formated incorrectly for single document scan') from e
