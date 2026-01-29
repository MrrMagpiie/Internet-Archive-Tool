from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot, QTimer, QThreadPool, Qt
from PyQt6.QtWidgets import QApplication
from queue import Queue
from pathlib import Path
import os
from model.service import *
from model.task import *
from model.service.DatabaseManager import DatabaseManager, DatabaseSignal
from model.service.DocumentPipeline import DocumentPipelineWorker, DocPipelineRequest
from model.service.UploadManager import UploadManager, UploadRequest
from model.data.document import Document
from model.data.schema import DocumentSchema
from config import user_config

from config import *
# ---------------- Process Manager ---------------
class ProcessManager(QObject):
    ia_setup_success = pyqtSignal(bool,str)
    db_update = pyqtSignal(Document)
    discovery_complete = pyqtSignal(dict)
    schema_loaded = pyqtSignal(object)
    schema_saved = pyqtSignal(object)
    need_setup = pyqtSignal()


    def __init__(self,parent=None):
        super().__init__(parent)
        self.active_pipelines = {}
        self.task_requests = {}
        self._db_setup()
        self._document_process_service()
        self._upload_manager_service()

    def start_task(task):
        QThreadPool.globalInstance().start(task)

    # tasks
    @pyqtSlot(object,QObject)
    def discover_task(self,data,requester):
        signals = discoverSignals()
        if hasattr(requester,'document'):
            signals.document.connect(requester.document)
        if hasattr(requester,'error'):
            signals.image_error.connect(requester.error)
            signals.doc_error.connect(requester.error)
        
        signals.image_error.connect(self.discover_error)
        signals.doc_error.connect(self.discover_error)

        # connect signals
        task = discoverTask(signals,dir)
        self.start_task(task)
    
    @pyqtSlot(DocumentSchema)
    def save_schema(self,schema):
        schema_dict = schema.to_dict()
        with open('/var/home/magpie/Development/Library2/resources/document_schema.json', 'r') as f: 
            data = json.load(f)

        with open('/var/home/magpie/Development/Library2/resources/document_schema.json', 'w') as f: 
            data[schema_dict.get('schema_name')] = schema_dict
            json.dump(data,f,indent=4)
    
    #Upload Manager
    def _upload_manager_service(self):
        self.upload_manager_thread = QThread()
        self.upload_manager_queue = Queue()
        self.upload_manager = UploadManager(self.upload_manager_queue)

        self.upload_manager.error.connect(self.upload_error)
        self.upload_manager.document.connect(self.upload_success)
        self.upload_manager.moveToThread(self.upload_manager_thread)

        self.upload_manager_thread.started.connect(self.upload_manager.run)
        self.upload_manager_thread.start()

        if user_config.get('IA_CONFIG'):
            os.environ['IA_CONFIG_FILE'] = user_config.get('IA_CONFIG')
        else:
            self.need_setup.emit()
    
    @pyqtSlot(Document)
    def upload_document(self,doc):
        signals = self._upload_signals(self)
        data = (signals,doc)
        print('uploading document')
        self.start_loading_cursor()
        self.upload_manager_queue.put(('upload',data))

    def _upload_signals(self,requester):
        signals = UploadRequest()
        if hasattr(requester,'upload_success'):
            signals.data.connect(requester.upload_success)
        if hasattr(requester,'upload_error'):
            signals.error.connect(requester.upload_error)
        return signals

    
    # Document Process
    @pyqtSlot(tuple,QObject)
    def send_document_process_request(self,data,requester):
        signals = self._doc_proccess_signals(requester)
        data = (signals,data)
        self.start_loading_cursor()
        self.doc_process_queue.put(('discover',data))

    def _document_process_service(self):
        self.doc_process_thread = QThread()
        self.doc_process_queue = Queue()
        self.document_worker = DocumentPipelineWorker(self.doc_process_queue)

        self.document_worker.error.connect(self.discover_error)
        self.document_worker.document.connect(self.doc_success)
        self.document_worker.moveToThread(self.doc_process_thread)

        self.doc_process_thread.started.connect(self.document_worker.run)
        self.doc_process_thread.start()

    def _doc_proccess_signals(self, requester):
        print(requester)
        signals = DocPipelineRequest()
        if hasattr(requester,'doc_return'):
            signals.data.connect(requester.doc_return)
        if hasattr(requester, 'doc_error'):
            signals.error.connect(requester.doc_error)
        return signals

    # Database_Manager
    def _db_setup(self):
        self.db_thread = QThread()
        self.db_queue = Queue()
        self.db_manager = DatabaseManager(DB_PATH, self.db_queue)
        self.db_manager.save_document.connect(self._db_update)
        self.db_manager.error.connect(self.database_error)
        self.db_manager.moveToThread(self.db_thread)
        
        # Connections
        self.db_thread.started.connect(self.db_manager.run)
        self.db_thread.start()

    def _db_signals(self,requester):
        signals = DatabaseSignal()
        if hasattr(requester,'doc_return'):
            signals.data.connect(requester.doc_return)
        if hasattr(requester,'doc_error'):
            signals.error.connect(requester.doc_error)
        return signals

    @pyqtSlot(object,QObject)
    def docs_by_status(self,filter_data,requester):
        signals = _db_signals(requester)
        data = (signals,filter_data)
        self.db_queue.put(('load_documents', data ))
   
    @pyqtSlot(str,QObject)
    def doc_by_id(self,doc_id,requester):
        signals = _db_signals(requester)
        data = (signals,doc_id)
        self.db_queue.put(('load_single_document',data))
    
    def update_doc(self,doc,requester = None):
        if requester != None:
            signals = self._db_signals(requester)
        else:
            signals = self._db_signals(self)
        data = (signals,doc)
        self.db_queue.put(('save_document',data))

    @pyqtSlot(str)
    def on_db_error(self, error_msg):
        print(f"Main Thread: DB Error: {error_msg}")
    
    @pyqtSlot(Document)
    def _db_update(self,doc):
        '''
        emits document to gui when database saves a document
        '''
        print('emit db_update')
        self.db_update.emit(doc)

    def closeEvent(self, event):
        """Properly shut down the thread on window close."""
        print("Main Thread: Shutting down worker...")
        # Send shutdown signal
        self.db_queue.put(('shutdown', None))
        
        # Tell the thread to quit
        self.db_thread.quit()
        
        # Wait for the thread to finish
        self.db_thread.wait() 
        event.accept()

    # Errors
    @pyqtSlot(str)
    def discover_error(self,error):
        self.stop_loading_cursor()
        print(f'discovery: {error}')

    @pyqtSlot(str)
    def database_error(self,error):
        print(f'error with database interaction:{error}')
    
    @pyqtSlot(Document)
    def doc_success(self,doc):
        self.stop_loading_cursor()
        self.update_doc(doc)
        print(f'doc success: {doc}')
    
    @pyqtSlot(str)
    def upload_error(self,error):
        self.stop_loading_cursor()
        print(f'document upload error: {error}')
    
    @pyqtSlot(Document)
    def upload_success(self,doc):
        self.stop_loading_cursor()
        print('document upload success')

    @pyqtSlot()
    def start_loading_cursor(self):
        """Helper to set the wait cursor."""
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
    
    @pyqtSlot()
    def stop_loading_cursor(self):
        """Helper to restore the default cursor."""
        # It's good practice to ensure we don't restore if not set, 
        # but restoreOverrideCursor is safe to call even if no override exists.
        QApplication.restoreOverrideCursor()