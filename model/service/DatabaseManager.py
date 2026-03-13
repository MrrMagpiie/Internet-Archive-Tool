import sqlite3
from pathlib import Path
from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import hashlib
import secrets

from model.data.document import Document

class DatabaseManager(QObject):
    """
    A QObject worker that manages all database interactions
    in a separate thread.
    """
    update = pyqtSignal(object,str)
    error = pyqtSignal(str,str) #error_msg, job_id
    prog = pyqtSignal(int)# progress

    def __init__(self, db_path: Path, queue: Queue):
        super().__init__()
        self.db_path = db_path
        self.queue = queue
        self.conn = None 
        print('init DatabaseManager')

    @pyqtSlot()
    def run(self):
        """The main worker loop. This runs in the QThread."""
        try:
            print('Database Manager queue running')
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            self._create_tables()

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
                            filter_data = data
                            docs = self._load_documents(filter_data)
                            if not signals.is_cancelled():
                                signals.data.emit(docs,signals.job_id)
                        case 'load_single_document':
                            doc_id = data
                            doc = self._load_single_document(doc_id)
                            if not signals.is_cancelled():
                                signals.data.emit(doc,signals.job_id)
                        case 'save_document':
                            document = data
                            self._save_document(document)
                            signals.data.emit(document,signals.job_id)
                            self.update.emit(document,signals.job_id)
                        case 'delete_document':
                            doc_id = data
                            self._delete_document(doc_id)
                            if not signals.is_cancelled():
                                signals.data.emit(doc_id, signals.job_id)
                                self.update.emit(doc_id, "deleted")
                        case 'verify_login':
                            username, password = data
                            success, role = self._verify_login(username, password)
                            
                            if not signals.is_cancelled():
                                result = {'success': success, 'role': role, 'username': username}
                                signals.data.emit(result, signals.job_id)

                        case 'new_user':
                            username, password = data
                            self._create_user(username, password)
                            if not signals.is_cancelled():
                                success, msg = self._create_user(username, password)
                                if success:
                                    # Tell the Wizard to finish!
                                    signals.data.emit(True, signals.job_id)
                                else:
                                    # Tell the Wizard it failed, and pass the error message!
                                    signals.error.emit(msg, signals.job_id)
                            
                
                except Exception as e:
                    signals.error.emit(f"Error processing command {command} for {signals.job_id}: {e}",signals.job_id)
                    self.error.emit((f"Error processing command {command} for {signals.job_id}: {e}"),signals.job_id)

        except Exception as e:
            self.error.emit(f"Database Worker-level error:  {e}","")
        finally:
            if self.conn:
                self.conn.close()

    def _create_user(self, username, password) -> tuple[bool, str]:
        """Generates a new user and safely handles duplicate usernames."""
        cursor = self.conn.cursor()
        salt = secrets.token_hex(16)
        hashed_pw = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000 
        ).hex()

        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, salt, role)
                VALUES (?, ?, ?, ?)
            ''', (username, hashed_pw, salt, 'admin'))
            
            self.conn.commit()
            return True, "User created successfully."
            
        except sqlite3.IntegrityError:
            # The username already exists! Roll back the transaction.
            self.conn.rollback()
            return False, f"The username '{username}' is already taken."
            
        except Exception as e:
            # Catch any other weird database errors (like a locked file)
            self.conn.rollback()
            return False, f"Database error: {str(e)}"


    def _create_tables(self):
        """Internal method to create tables. Called by run()."""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                metadata INTEGER NOT NULL DEFAULT 0,
                deskewed INTEGER NOT NULL DEFAULT 0,
                needs_approval INTEGER NOT NULL DEFAULT 0,
                approved INTEGER NOT NULL DEFAULT 0,
                rejected INTEGER NOT NULL DEFAULT 0,
                uploaded INTEGER NOT NULL DEFAULT 0,
                path TEXT,
                metadata_file TEXT,
                metadata_file_type TEXT,
                last_modified TEXT NOT NULL,
                error_msg TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user' 
                )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                image_id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                sort_order TEXT,
                original_path TEXT NOT NULL,
                processed_path TEXT NOT NULL,
                FOREIGN KEY (doc_id) REFERENCES documents (doc_id) ON DELETE CASCADE
            )
        ''')
            
        self.conn.commit()


    def _load_documents(self, filter_status: dict[str, bool] | None = None) -> dict[str, Document]:
        """Internal method. Loads documents and their images."""
        docs = {}
        cursor = self.conn.cursor()
        
        sql_query = "SELECT doc_id, metadata, deskewed, needs_approval, approved, rejected, uploaded, path, metadata_file, metadata_file_type, last_modified, error_msg FROM documents"
        params = []
        
        if filter_status:
            conditions = []
            for status_key, status_value in filter_status.items():
                db_value = 1 if status_value else 0
                conditions.append(f"{status_key} = ?")
                params.append(db_value)
            
            if conditions:
                sql_query += " WHERE " + " AND ".join(conditions)

        cursor.execute(sql_query, tuple(params))
        
        for row in cursor.fetchall():
            doc_id, metadata, deskewed, needs_approval, approved, rejected, uploaded, path, metadata_file, metadata_file_type, last_modified, error_msg = row
            status = { 
                'metadata': bool(metadata),
                'deskewed': bool(deskewed),
                'needs_approval': bool(needs_approval),
                'approved': bool(approved),
                'rejected': bool(rejected),
                'uploaded': bool(uploaded)
            }
            docs[doc_id] = Document(doc_id=doc_id, status=status, path=path, metadata_file=metadata_file, metadata_file_type=metadata_file_type, last_modified=last_modified, error_msg=error_msg)
            
        if docs:
            doc_ids = tuple(docs.keys())
            placeholders = ','.join('?' for _ in doc_ids)
            
            image_query = f"SELECT image_id, doc_id, sort_order, original_path, processed_path FROM images WHERE doc_id IN ({placeholders})"
            cursor.execute(image_query, doc_ids)
            
            for row in cursor.fetchall():
                image_id, doc_id, order, orig_path, proc_path = row
                if doc_id in docs:
                    docs[doc_id].add_image(image_id, order, orig_path, proc_path)
        
        return docs

    def _load_single_document(self, doc_id: str) -> Document | None:
        """Internal method. Loads a single document by its ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT doc_id, metadata, deskewed, needs_approval, approved, rejected, uploaded, path, metadata_file, metadata_file_type, last_modified, error_msg FROM documents WHERE doc_id = ?", (doc_id,))
        doc_row = cursor.fetchone()
        
        if not doc_row:
            return None

        # ... (rest of the row parsing is identical) ...
        doc_id, metadata, deskewed, needs_approval, approved, rejected, uploaded, path, metadata_file, metadata_file_type, last_modified, error_msg = doc_row
        status = {
            'metadata': bool(metadata),
            'deskewed': bool(deskewed),
            'needs_approval': bool(needs_approval),
            'approved': bool(approved),
            'rejected': bool(rejected),
            'uploaded': bool(uploaded)
        }
        doc = Document(doc_id=doc_id, status=status, path=path, metadata_file=metadata_file, metadata_file_type=metadata_file_type, last_modified=last_modified, error_msg=error_msg)
        
        cursor.execute("SELECT image_id, sort_order, original_path, processed_path FROM images WHERE doc_id = ?", (doc_id,))
        for row in cursor.fetchall():
            image_id, order, orig_path, proc_path = row
            doc.addImage(image_id, order, orig_path, proc_path)
        return doc


    def _delete_document(self, doc_id: str):
        """Internal method. Removes a document and cascades the deletion to its images."""
        cursor = self.conn.cursor()
        
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        cursor.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        self.conn.commit()

    def _save_document(self, doc: Document):
        """Internal method. Saves a single Document object."""
        cursor = self.conn.cursor()
        status = doc.status
        params_tuple = (
                doc.doc_id,  
                int(status.get('metadata', 0)),
                int(status.get('deskewed', 0)), 
                int(status.get('needs_approval', 0)),
                int(status.get('approved', 0)), 
                int(status.get('rejected', 0)),
                int(status.get('uploaded', 0)), 
                str(doc.path), 
                str(doc.metadata_file) if doc.metadata_file else None, 
                str(doc.metadata_file_type) if doc.metadata_file_type else None, 
                doc.last_modified, doc.error_msg if doc.error_msg else None
                )

        cursor.execute('''
            INSERT OR REPLACE INTO documents (doc_id, metadata, deskewed, needs_approval,
            approved, rejected, uploaded, path, metadata_file, metadata_file_type, last_modified, error_msg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',params_tuple )
        
        for image_id, image_data in doc.images.items():
            cursor.execute('''
                INSERT OR REPLACE INTO images (image_id, doc_id, sort_order, original_path, processed_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (image_id, doc.doc_id, image_data['order'], image_data['original'], image_data['processed']))
        self.conn.commit()

    import hashlib

    def _verify_login(self, username, plaintext_password) -> tuple[bool, str | None]:
        """
        Hashes the incoming password and compares it to the database.
        Returns (True, role) if successful, (False, None) if failed.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT password_hash, salt, role FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        # Username doesn't exist
        if not row:
            return False, None
            
        stored_hash, salt, role = row
        
        # Hash the attempted password using the exact same algorithm and salt
        test_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            plaintext_password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000
        ).hex()
        
        # Compare the hashes
        if test_hash == stored_hash:
            return True, role
            
        return False, None


    def cancel_current_query(self):
        """Called by the main GUI thread to instantly abort the active SQLite query."""
        if self.conn:
            self.conn.interrupt()