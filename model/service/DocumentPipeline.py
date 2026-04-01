from sqlite3 import OperationalError
from pathlib import Path
from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import traceback
import multiprocessing
import shutil

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

                        case 'batch_discover':
                            in_dir = data
                            self.batch_discover(in_dir, signals)

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

                        case 'delete':
                            doc_path = data
                            if isinstance(doc_path,Path):
                                self.delete_document_files(doc_path)
                                signals.data.emit(None,signals.job_id)
                                self.success.emit(None,signals.job_id)
                        case _:
                            raise ValueError(f"Worker {self} received an unknown command: {command}")
                
                except TaskCancelledError:
                    print(f"Job {signals.job_id} was safely aborted.")

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
            
    def batch_discover(self,in_dir,signals):
            image_list = discover_images(in_dir)
            try:
                documents_dict = images_to_documents(image_list)
            except Exception as e:
                raise ImageDiscoveryError(f'Images to Document Error') from e

            for doc_id in documents_dict.keys():
                try:
                    doc = create_document(doc_id,documents_dict[doc_id])
                    if isinstance(doc,Document) and  not signals.is_cancelled():
                        signals.data.emit(doc,signals.job_id)
                        self.success.emit(doc,signals.job_id)
                except Exception as e:
                    raise DocumentCreationError(f'Document Creation Error: {doc_id}')

    def deskew(self, doc: Document, ticket: JobTicket):
        """Runs inside your PyQt QThread Worker."""
        doc_directory = Path(doc.path)
        doc_directory.mkdir(parents=True, exist_ok=True)
        
        try:
            for image_id, image_task in doc.images.items():
                in_file = Path(image_task["original"])
                out_file = Path(image_task["processed"])

                queue = multiprocessing.Queue()
                self.process = multiprocessing.Process(
                    target=deskew_image,
                    args=(str(in_file), str(out_file), queue) 
                )
                self.process.start()

                while self.process.is_alive():
                    if ticket.is_cancelled():
                        self.process.terminate() 
                        self.process.join()
                        raise TaskCancelledError()
                    
                    self.process.join(timeout=0.2) 

                if not queue.empty():
                    result = queue.get() 
                    
                    if result['status'] == 'success':
                        angle = result['angle']
                        doc.add_change(image_id, f'deskew: {angle}')
                        print(f'Deskewed {image_id} in {doc.doc_id} by {angle} degrees')
                    else:
                        raise DeskewError(in_file,out_file,result['error'])
                else:
                    raise DeskewError(in_file,out_file,"The deskew process crashed without returning data.")

            return doc

        except DeskewError as e:
            e.doc_id = doc.doc_id
            raise

        finally:
            queue.close()
            queue.join_thread()
    
    def delete_document_files(self,document_path) -> bool:
        """
        deletes all physical files associated with a Document.
        """        
        parent_dir = Path(document_path)
        if parent_dir.exists() and parent_dir.is_dir():
            try:
                shutil.rmtree(parent_dir)
            except Exception as e:
                raise DocumentDeletionError(f"Failed to delete directory") from e