from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot, QTimer, QThreadPool
from queue import Queue
from pathlib import Path
from model.service import *
from model.task import *
from model.service.DatabaseManager import DatabaseManager, DatabaseSignal
from model.service.DocumentPipeline import DocumentPipelineWorker, DocPipelineRequest
from model.data.document import Document

from config import *
# ---------------- Process Manager ---------------
class ProcessManager(QObject):
    ia_setup_success = pyqtSignal(bool,str)
    db_update = pyqtSignal(Document)
    discovery_complete = pyqtSignal(dict)
    schema_loaded = pyqtSignal(object)
    schema_saved = pyqtSignal(object)


    def __init__(self,parent=None):
        super().__init__(parent)
        self.active_pipelines = {}
        self.task_requests = {}
        self._db_setup()
        self._document_process_service()


    def start_task(task):
        QThreadPool.globalInstance().start(task)

    # tasks
    @pyqtSlot(object,QObject)
    def discover_task(data,requester):
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
    
    @pyqtSlot(tuple,QObject)
    def start_document_process(self,data,requester):
        signals = self._doc_proccess_signals(requester)
        data = (signals,data)
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
        print(f'discovery: {error}')

    @pyqtSlot(str)
    def database_error(self,error):
        print(f'error with database interaction:{error}')
    
    @pyqtSlot(Document)
    def doc_success(self,doc):
        self.update_doc(doc)
        print(f'doc success: {doc}')