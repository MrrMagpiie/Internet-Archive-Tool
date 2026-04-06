from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from model.service.db_providers import AbstractDatabaseProvider
from model.data.document import Document


class DatabaseWorker(QObject):
    """
    A QObject worker that manages all database interactions
    in a separate thread.
    """
    update = pyqtSignal(object,str)
    error = pyqtSignal(Exception,str) #error_msg, job_id
    prog = pyqtSignal(int)# progress

    def __init__(self, provider: AbstractDatabaseProvider, queue: Queue):
        super().__init__()
        self.provider = provider
        self.queue = queue
        print('init DatabaseWanager')

    @pyqtSlot()
    def run(self):
        """The main worker loop. This runs in the QThread."""
        try:
            print('Database Manager queue running')
            self.provider.connect()

            while True:
                command, signals, data = self.queue.get()
                if command == 'shutdown':
                    break 
                if signals.is_cancelled():
                            continue
                print(f'db running {command}')
                
                try:
                    match command: 
                        case 'load_documents':
                            docs = self.provider.load_documents(data)
                            if not signals.is_cancelled():
                                signals.data.emit(docs, signals.job_id)
                        case 'save_document':
                            self.provider.save_document(data)
                            signals.data.emit(data,signals.job_id)
                            self.update.emit(data,signals.job_id)
                        case 'delete_document':
                            self.provider.delete_document(data)
                            if not signals.is_cancelled():
                                signals.data.emit(data, signals.job_id)
                                self.update.emit(data, signals.job_id)
                        case 'verify_login':
                            username, password = data
                            success, role = self.provider.verify_login(username, password)
                            
                            if not signals.is_cancelled():
                                result = {'success': success, 'role': role, 'username': username}
                                signals.data.emit(result, signals.job_id)
                        case 'new_user':
                            username, password, role = data
                            if not signals.is_cancelled():
                                success, msg = self.provider.create_user(username, password, role)
                                if success:
                                    signals.data.emit(True, signals.job_id)
                                else:
                                    signals.error.emit(msg, signals.job_id)
                        case 'get_users':
                            if not signals.is_cancelled():
                                users = self.provider.get_users()
                                signals.data.emit(users, signals.job_id)
                        case 'delete_user':
                            if not signals.is_cancelled():
                                success, msg = self.provider.delete_user(data)
                                if success:
                                    signals.data.emit(True, signals.job_id)
                                else:
                                    signals.error.emit(msg, signals.job_id)
                        case 'check_admin':
                            if not signals.is_cancelled():
                                signals.data.emit(self.provider.has_admin(), signals.job_id)


                except Exception as e:
                    if "interrupted" in str(e).lower():
                        print(f"Database query for {signals.job_id} was successfully aborted.")
                        signals.error.emit("Cancelled by user", signals.job_id)
                    else:
                        signals.error.emit(str(e), signals.job_id)
                        self.error.emit(e, signals.job_id)

        except Exception as e:
            self.error.emit(e,'')
        finally:
            self.provider.disconnect()
            
    def has_admin_sync(self) -> bool:
        return self.provider.has_admin_sync()
        
    def cancel_current_query(self):
        self.provider.cancel_current_query()