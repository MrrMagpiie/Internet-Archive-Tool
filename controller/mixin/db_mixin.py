from PyQt6.QtCore import QThread, pyqtSlot, pyqtSignal,QObject
from queue import Queue
from model.service.DatabaseManager import DatabaseManager
from model.service.signals import JobTicket, DatabaseTicket
from config import DB_PATH

class DatabaseMixin:
    """Handles Database Worker logic."""
    
    def setup_database(self):
        self.db_thread = QThread()
        self.db_queue = Queue()
        self.db_manager = DatabaseManager(DB_PATH, self.db_queue)
        
        self.db_manager.update.connect(self._handle_database_update)
        self.db_manager.error.connect(self._handle_worker_error)
        
        self.db_manager.moveToThread(self.db_thread)
        self.db_thread.started.connect(self.db_manager.run)
        self.db_thread.start()

    @pyqtSlot(object, QObject)
    def request_docs_by_status(self, filter_data, ticket:DatabaseTicket):
        ticket.interupt.connect(self.db_interupt)
        self.register_task('load_documents', ticket)
        self.db_queue.put(('load_documents', ticket, filter_data))
   
    @pyqtSlot(str, QObject)
    def request_doc_by_id(self, doc_id, ticket:DatabaseTicket):
        ticket.interupt.connect(self.db_interupt)
        filter_data = {'doc_id': doc_id}
        self.register_task('load_documents', ticket)
        self.db_queue.put(('load_documents', ticket, filter_data))
    
    @pyqtSlot(object,QObject)
    def request_update_doc(self, doc, ticket:DatabaseTicket):
        ticket.interupt.connect(self.db_interupt)
        self.register_task('save_document', ticket)
        self.db_queue.put(('save_document', ticket, doc))

    @pyqtSlot()
    def db_interupt():
        self.db_manager.cancel_current_query()

    @pyqtSlot(object,str)
    def _handle_database_update(self, doc,job_id):
        if isinstance(doc,Document):
            self.document_update.emit(doc)
        elif isinstance(doc,str):
            self.document_delete.emit(doc)

    def shutdown_database(self):
        self.db_queue.put(('shutdown', None, None))
        self.db_thread.quit()
        self.db_thread.wait()