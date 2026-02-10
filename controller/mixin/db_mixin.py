from PyQt6.QtCore import QThread, pyqtSlot, pyqtSignal,QObject
from queue import Queue
from model.service.DatabaseManager import DatabaseManager, DatabaseSignal
from config import DB_PATH

class DatabaseMixin:
    """Handles Database Worker logic."""
    
    def setup_database(self):
        self.db_thread = QThread()
        self.db_queue = Queue()
        self.db_manager = DatabaseManager(DB_PATH, self.db_queue)
        
        # Connect Internal Signals
        self.db_manager.save_document.connect(self._handle_db_update)
        self.db_manager.error.connect(self._handle_worker_error)
        
        self.db_manager.moveToThread(self.db_thread)
        self.db_thread.started.connect(self.db_manager.run)
        self.db_thread.start()

    @pyqtSlot(object, QObject)
    def request_docs_by_status(self, filter_data, requester):
        signals = self._attach_signals(DatabaseSignal(), requester, {'data': 'doc_return', 'error': 'doc_error'})
        self.db_queue.put(('load_documents', (signals, filter_data)))
   
    @pyqtSlot(str, QObject)
    def request_doc_by_id(self, doc_id, requester):
        signals = self._attach_signals(DatabaseSignal(), requester, {'data': 'doc_return', 'error': 'doc_error'})
        self.db_queue.put(('load_single_document', (signals, doc_id)))
    
    @pyqtSlot(object,QObject)
    def request_update_doc(self, doc, requester=None):
        signals = self._attach_signals(DatabaseSignal(), requester, {'data': 'doc_return', 'error': 'doc_error'})
        self.db_queue.put(('save_document', (signals, doc)))

    @pyqtSlot(object)
    def _handle_db_update(self, doc):
        """Re-emits the update so the whole UI knows a doc changed."""
        self.db_update.emit(doc)

    def shutdown_database(self):
        self.db_queue.put(('shutdown', None))
        self.db_thread.quit()
        self.db_thread.wait()