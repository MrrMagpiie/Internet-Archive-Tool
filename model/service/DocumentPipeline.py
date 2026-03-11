from sqlite3 import OperationalError
from pathlib import Path
from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from model.data.document import Document
from model.logic.discover import *
from model.logic.deskew import *
from model.logic.metadata import *

class DocPipelineRequest(QObject):
    data = pyqtSignal(str,Document)# Document Return
    error = pyqtSignal(str)# Error Message Return
    prog = pyqtSignal(int)# progress update

class DocumentPipelineWorker(QObject):
    """
    A QObject worker that runs the full document pipeline
    """
    success = pyqtSignal(Document,str) # job_id
    error = pyqtSignal(str,str) # error_msg job_id 
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
                            in_dir, out_dir = data
                            doc = self.discover(in_dir,out_dir)
                            if isinstance(doc,Document) and  not signals.is_cancelled():
                                signals.data.emit(doc,signals.job_id)
                                self.success.emit(doc,signals.job_id)
                            
                        case 'metadata':
                            doc, metadata, metadata_type = data
                            if isinstance(doc,Document):
                                doc = add_metadata_to_document(doc, metadata,metadata_type)
                                doc.status['metadata'] = True
                            if not signals.is_cancelled():
                                signals.data.emit(doc,signals.job_id)
                                self.success.emit(doc,signals.job_id)

                        case 'deskew':
                            doc = data
                            if isinstance(doc,Document):
                                self.deskew(doc)
                                doc.status['deskewed'] = True
                            if not signals.is_cancelled():
                                signals.data.emit(doc,signals.job_id)
                                self.success.emit(doc,signals.job_id)

                except Exception as e:
                    err_msg =f"Error processing command {command} for {signals.job_id}: {e}"
                    signals.error.emit(err_msg,signals.job_id)
                    self.error.emit(err_msg,signals.job_id)

                except sqlite3.OperationalError as e:
                    if "interrupted" in str(e).lower():
                        print(f"Database query for {signals.job_id} was successfully aborted.")
                        signals.error.emit("Cancelled by user", signals.job_id)
                    else:
                        signals.error.emit(f"SQLite Error: {e}", signals.job_id)

        except Exception as e:
            self.error.emit(f"Document Worker-level error:  {e}",'')

    def discover(self,in_dir,out_dir):
            image_list = discover_images(in_dir)

            try:
                documents_dict = images_to_documents(image_list)
            except Exception as e:
                self.error.emit(f'Images to Document Error: {e}')

            if len(documents_dict.keys()) == 1:
                for doc_id in documents_dict.keys():
                    try:
                        doc = create_document(doc_id,documents_dict[doc_id])
                        return doc
                    except Exception as e:
                        raise(f'Document Creation Error: {doc_id}',{e})
            else:
                print('more that one Doc in folder')
                return False
            
    def deskew(self,doc:Document):
        try:
            deskew_document(doc)
        except Exception as e:
            raise(f'Deskewing Error: {doc.doc_id},{e}')
    
