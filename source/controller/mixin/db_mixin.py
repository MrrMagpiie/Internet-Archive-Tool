from PyQt6.QtCore import QThread, pyqtSlot, pyqtSignal,QObject
from queue import Queue
from model.service.DatabaseManager import DatabaseManager
from model.service.Signals import JobTicket, DatabaseTicket
from config import DB_PATH
from functools import partial
from model.data.document import Document


class DatabaseMixin:
    """Handles Database Worker logic."""
    
    def setup_database(self):
        self.need_db = not DB_PATH.exists()
        self.db_thread = QThread()
        self.db_queue = Queue()
        self.db_manager = DatabaseManager(DB_PATH, self.db_queue)

        #check for admin account if db exists
        if not self.need_db:
            self.need_db = not self.db_manager.has_admin_sync()
        
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

    @pyqtSlot(Document,QObject)
    def request_delete_doc(self, doc, ticket:DatabaseTicket):
        ticket.interupt.connect(self.db_interupt)
        delete_files = partial(self.request_delete_document_files,doc_path = doc.path, ticket = ticket)
        ticket.data.connect(delete_files)
        self.register_task('delete_document', ticket)
        self.db_queue.put(('delete_document', ticket, doc.doc_id))
    
    @pyqtSlot(Document,QObject)
    def request_remove_doc(self, doc, ticket:DatabaseTicket):
        ticket.interupt.connect(self.db_interupt)
        self.register_task('delete_document', ticket)
        self.db_queue.put(('delete_document', ticket, doc.doc_id))

    @pyqtSlot(tuple,DatabaseTicket)
    def request_login(self,data, ticket:DatabaseTicket):
        ticket.interupt.connect(self.db_interupt)
        self.register_task('verify_login', ticket)
        self.db_queue.put(('verify_login', ticket, data))
        
    @pyqtSlot(tuple,DatabaseTicket)
    def new_user(self,data,ticket:DatabaseTicket):
        ticket.interupt.connect(self.db_interupt)
        self.register_task('new_user', ticket)
        self.db_queue.put(('new_user', ticket, data))

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