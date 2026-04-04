from sqlite3 import OperationalError
from pathlib import Path
from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import traceback
import multiprocessing
import shutil

from model.data.document import Document, update_metadata_file
from model.logic.discover import images_to_documents, get_image_list
from model.logic.deskew import deskew_task
from model.exceptions import DeskewError, ImageDiscoveryError, DocumentCreationError, DocumentDeletionError, TaskCancelledError
from model.service.Signals import JobTicket
from model.settings_manager import app_settings

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
                            doc = self.single_discover(in_dir, signals)
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

    def single_discover(self, in_dir, ticket):
            ticket.update_progress(10, "Scanning directory for images...")
            image_list = get_image_list(in_dir)

            try:
                ticket.update_progress(40, "Grouping images into documents...")
                documents_dict = images_to_documents(image_list)
            except Exception as e:
                raise ImageDiscoveryError() from e

            if len(documents_dict.keys()) == 1:
                for doc_id, image_list in documents_dict.items():
                    try:
                        ticket.update_progress(80, "Building document structure...")
                        doc = Document.from_images(doc_id,image_list)
                        doc.set_output_path(Path(app_settings.get('DEFAULT_OUTPUT_DIR')) / doc_id)
                        doc.path.mkdir(parents=True, exist_ok=True)
                        ticket.update_progress(100, "Discovery Complete!")
                        return doc
                    except Exception as e:
                        raise DocumentCreationError(doc_id)
            else:
                raise ImageDiscoveryError('Directory formated incorrectly for single document scan')
            
    def batch_discover(self, in_dir, ticket):
            ticket.update_progress(10, "Scanning directory for images...")
            image_list = get_image_list(in_dir)
            try:
                ticket.update_progress(30, "Grouping images into documents...")
                documents_dict = images_to_documents(image_list)
            except Exception as e:
                raise ImageDiscoveryError(f'Images to Document Error') from e

            items = list(documents_dict.items())
            total = len(items)
            for i, (doc_id, image_list) in enumerate(items):
                ticket.update_progress(30 + int((i / total) * 70), f"Processing document {i+1}/{total}...")
                try:
                    doc = Document.from_images(doc_id, image_list)
                    doc.set_output_path(Path(app_settings.get('DEFAULT_OUTPUT_DIR')) / doc_id)
                    doc.path.mkdir(parents=True, exist_ok=True)
                    if isinstance(doc,Document) and  not ticket.is_cancelled():
                        ticket.data.emit(doc,ticket.job_id)
                        self.success.emit(doc,ticket.job_id)
                except Exception as e:
                    raise DocumentCreationError(f'Document Creation Error: {doc_id}')
            
            ticket.update_progress(100, "Batch Discovery Complete!")

    def deskew(self, doc: Document, ticket: JobTicket):
        """Runs inside your PyQt QThread Worker."""
        doc_directory = Path(doc.path)
        doc_directory.mkdir(parents=True, exist_ok=True)
        
        try:
            images_items = list(doc.images.items())
            total = len(images_items)
            
            for i, (image_id, image_task) in enumerate(images_items):
                ticket.update_progress(int((i / total) * 100), f"Deskewing page {i+1}/{total}...")
                in_file = Path(image_task["original"])
                out_file = Path(image_task["processed"])

                queue = multiprocessing.Queue()
                self.process = multiprocessing.Process(
                    target=deskew_task,
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

            ticket.update_progress(100, "Deskew Complete!")
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