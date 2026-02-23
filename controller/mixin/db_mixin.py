from PyQt6.QtCore import QThread, pyqtSlot, pyqtSignal,QObject
from queue import Queue
from model.service.DatabaseManager import DatabaseManager
from model.service.signals import JobTicket
from config import DB_PATH

class DatabaseMixin:
    """Handles Database Worker logic."""
    
    def setup_database(self):
        self.db_thread = QThread()
        self.db_queue = Queue()
        self.db_manager = DatabaseManager(DB_PATH, self.db_queue)
        
        # Connect Internal ticket
        self.db_manager.update.connect(self._handle_db_update)
        self.db_manager.error.connect(self._handle_worker_error)
        
        self.db_manager.moveToThread(self.db_thread)
        self.db_thread.started.connect(self.db_manager.run)
        self.db_thread.start()

    @pyqtSlot(object, QObject)
    def request_docs_by_status(self, filter_data, ticket):
        self.db_queue.put(('load_documents', (ticket, filter_data)))
   
    @pyqtSlot(str, QObject)
    def request_doc_by_id(self, doc_id, ticket):
        self.db_queue.put(('load_single_document', (ticket, doc_id)))
    
    @pyqtSlot(object,QObject)
    def request_update_doc(self, doc, ticket=None):
        if not ticket:
            ticket = JobTicket()
        self.db_queue.put(('save_document', (ticket, doc)))

    @pyqtSlot(object,str)
    def _handle_db_update(self, doc,job_id):
        """Re-emits the update so the whole UI knows a doc changed."""
        self.db_update.emit(doc)

    def shutdown_database(self):
        self.db_queue.put(('shutdown', None))
        self.db_thread.quit()
        self.db_thread.wait()