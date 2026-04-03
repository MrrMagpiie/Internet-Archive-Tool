from queue import Queue, Empty
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from model.logic.upload import *
from model.exceptions import MetadataError, PdfGenerationError, TaskCancelledError
from model.data import Document, get_metadata_from_file, update_metadata_file
from model.service.Signals import JobTicket

import sys
import multiprocessing
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
                            self.upload_document(doc,signals)
                            doc.status['uploaded'] = True
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

    def upload_document(self, doc: Document, ticket: JobTicket):
        if doc.metadata is None and not Path(doc.metadata_file).is_file():
            raise MetadataError("Metadata file not found",doc.doc_id)
        '''elif doc.metadata is None:
            doc.add_metadata(get_metadata_from_file(doc))'''
        
        queue = multiprocessing.Queue()
        
        try:
            self.process = multiprocessing.Process(
                target=build_IA_payload,
                args=(doc.doc_id, doc.images, doc.path, queue)
            )
            self.process.start()

            success = False
            while True:
                if ticket.is_cancelled():
                    self.process.terminate()
                    self.process.join()
                    raise TaskCancelledError("Upload cancelled during PDF generation.")
                
                try:
                    result = queue.get(timeout=0.2)
                    match result['status']:
                        case 'success':
                            zip_path = result['zip_path']
                            pdf_path = result['pdf_path']
                            success = True
                        case 'error':
                            raise result['error']
                        case 'zip_progress':
                            scaled_progress = 30 + int((result['progress'] / 100) * 40)
                            ticket.update_progress(scaled_progress, result['step'])
                        case 'pdf_progress':
                            scaled_progress = 70 + int((result['progress'] / 100) * 30)
                            ticket.update_progress(70, result['step'])
                        case _:
                            raise ValueError(f"Unknown status: {result['status']}")
                except Empty:
                    if not self.process.is_alive():
                        break

            self.process.join()
            if not success:
                raise PdfGenerationError("Payload generation Worker crashed silently.")
                
        finally:
            queue.close()
            queue.join_thread()

        ticket.update_progress(70, "Uploading to Internet Archive...")
        
        if ticket.is_cancelled():
             raise TaskCancelledError("Cancelled before upload started.")
             
        # Intercept stderr to catch tqdm progress from the internetarchive library
        original_stderr = sys.stderr
        sys.stderr = ticket.interceptor(70, 100, 2)
        try:
            self.check_DEV_MODE(doc)
            response = upload(doc.metadata.to_dict(), [zip_path, str(pdf_path)])
        finally:
            sys.stderr = original_stderr
        
        ticket.update_progress(100, "Upload Complete!")

    def check_DEV_MODE(self,document:Document):
        metadata_dict = document.metadata.to_dict()
        if DEV_MODE:
            print("DEV MODE ACTIVE: Redirecting upload to test_collection...")
            metadata_dict['collection'] = 'test_collection'
            current_identifier = metadata_dict['identifier'] 
            metadata_dict['identifier'] = f"{current_identifier}_TEST"
            document.add_metadata(metadata_dict)
            update_metadata_file(document)