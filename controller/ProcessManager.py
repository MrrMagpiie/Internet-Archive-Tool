from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot, QTimer, QThreadPool
from queue import Queue
from pathlib import Path
from model.service import *
from model.task import *
from model.service.DatabaseManager import DatabaseManager
from model.data.document import Document

from config import *
# ---------------- Process Manager ---------------
class ProcessManager(QObject):
    ia_setup_success = pyqtSignal(bool,str)
    db_update = pyqtSignal(dict)
    discovery_complete = pyqtSignal(dict)
    schema_loaded = pyqtSignal(object)
    schema_saved = pyqtSignal(object)


    def __init__(self,parent=None):
        super().__init__(parent)
        self.active_pipelines = {}
        self.task_requests = {}
        self._db_setup()


    def start_task(task):
        QThreadPool.globalInstance().start(task)

    # tasks
    def discover_task(dir):
        signals = discoverSignals()
        # connect signals
        task = discoverTask(signals,dir)
        self.start_task(task)
 
    # Database_Manager

    def _db_setup(self):
        self.db_thread = QThread()
        self.db_queue = Queue()
        db_manager = DatabaseManager(DB_PATH, self.db_queue)
        db_manager.moveToThread(self.db_thread)
        
        # Connections
        self.db_thread.started.connect(db_manager.run)
        '''self.db_manager.documents.connect(self.on_documents_loaded)
        self.db_manager.error.connect(self.on_db_error)
        '''
        self.db_thread.start()

    @pyqtSlot(object,object)
    def request_documents(self,filter_data,signals):
        data = (signals,filter_data)
        self.db_queue.put(('load_documents', data ))

    def request_document(self,doc_id,signals):
        data = (signals,doc_id)
        self.db_queue.put(('load_single_document',data))
    
    @pyqtSlot(str)
    def on_db_error(self, error_msg):
        print(f"Main Thread: DB Error: {error_msg}")
        self.list_widget.addItem(f"ERROR: {error_msg}")
    
    @pyqtSlot(list)
    def _db_update(status_list):
        '''
        takes a list of types of documents updated and sends out signal to components to update
        '''
        self.db_update.emit(status_list)

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