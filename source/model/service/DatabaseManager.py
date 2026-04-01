import sqlite3
from pathlib import Path
from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import hashlib
import secrets
import json

from model.data.document import Document
from model.data.metadata import Metadata
from model.logic.metadata import update_metadata_file

VALID_FILTERS = {
    'doc_id', 'metadata', 'deskewed', 'needs_approval', 'approved', 
    'rejected', 'uploaded', 'path', 'metadata_file', 'metadata_file_type', 
    'metadata_json', 'last_modified', 'error_msg'
}

class DatabaseManager(QObject):
    """
    A QObject worker that manages all database interactions
    in a separate thread.
    """
    update = pyqtSignal(object,str)
    error = pyqtSignal(Exception,str) #error_msg, job_id
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
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys = ON;")
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
                                signals.data.emit(docs, signals.job_id)
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
                                self.update.emit(doc_id, signals.job_id)
                        case 'verify_login':
                            username, password = data
                            success, role = self._verify_login(username, password)
                            
                            if not signals.is_cancelled():
                                result = {'success': success, 'role': role, 'username': username}
                                signals.data.emit(result, signals.job_id)

                        case 'new_user':
                            username, password = data
                            if not signals.is_cancelled():
                                success, msg = self._create_user(username, password)
                                if success:
                                    signals.data.emit(True, signals.job_id)
                                else:
                                    signals.error.emit(msg, signals.job_id)
                            

                except sqlite3.OperationalError as e:
                    if "interrupted" in str(e).lower():
                        print(f"Database query for {signals.job_id} was successfully aborted.")
                        signals.error.emit("Cancelled by user", signals.job_id)
                    else:
                        signals.error.emit(f"SQLite Error: {e}", signals.job_id)
                
                except Exception as e:
                    signals.error.emit(e,signals.job_id)
                    self.error.emit(e,signals.job_id)

        except Exception as e:
            self.error.emit(e,'')
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
            # The username already exists Roll back the transaction.
            self.conn.rollback()
            return False, f"The username '{username}' is already taken."
            
        except Exception as e:
            # Catch any other database errors (like a locked file)
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
                metadata_json TEXT,
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
                changes TEXT,
                FOREIGN KEY (doc_id) REFERENCES documents (doc_id) ON DELETE CASCADE
            )
        ''')
            
        # Safely migrate existing databases to include new columns if missing
        # will need to be expanded to cover other possible changes
        cursor.execute("PRAGMA table_info(documents)")
        existing_columns = {col[1] for col in cursor.fetchall()}
        
        if 'metadata_json' not in existing_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN metadata_json TEXT")

        self.conn.commit()
    
    def _load_documents(self, filters: dict = None) -> dict[str, Document]:
        """method for fetching documents. Safely uses parameterized queries with a column whitelist."""
        docs = {}
        cursor = self.conn.cursor()
        
        sql_query = "SELECT doc_id, metadata, deskewed, needs_approval, approved, rejected, uploaded, path, metadata_file, metadata_file_type, metadata_json, last_modified, error_msg FROM documents"
        params = []
        
        if filters:
            conditions = []
        
            for key, value in filters.items():
                if key != 'or_filters':
                    if key not in VALID_FILTERS:
                        raise ValueError(f"Invalid filter column: {key}")
                    db_value = 1 if value is True else (0 if value is False else value)
                    conditions.append(f"{key} = ?")
                    params.append(db_value)
            
            if 'or_filters' in filters:
                or_conditions = []
                for or_key, or_value in filters['or_filters'].items():
                    if or_key not in VALID_FILTERS:
                        raise ValueError(f"Invalid filter column: {or_key}")
                    db_value = 1 if or_value is True else (0 if or_value is False else or_value)
                    or_conditions.append(f"{or_key} = ?")
                    params.append(db_value)
                
                if or_conditions:
                    or_string = " OR ".join(or_conditions)
                    conditions.append(f"({or_string})")
            
            if conditions:
                sql_query += " WHERE " + " AND ".join(conditions)

        cursor.execute(sql_query, tuple(params))
        for row in cursor.fetchall():
            doc = Document.from_db_row(row)
            docs[doc.doc_id] = doc
            
        if docs:
            doc_ids = tuple(docs.keys())
            placeholders = ','.join('?' for _ in doc_ids)
            
            image_query = f"SELECT image_id, doc_id, sort_order, original_path, processed_path, changes FROM images WHERE doc_id IN ({placeholders})"
            cursor.execute(image_query, doc_ids)
            
            for row in cursor.fetchall():
                image_id = row['image_id']
                doc_id = row['doc_id']
                order = row['sort_order']
                orig_path = row['original_path']
                proc_path = row['processed_path']
                changes = row['changes']
                
                if changes:
                    changes = json.loads(changes)
                if doc_id in docs:
                    docs[doc_id].add_image(image_id, order, orig_path, proc_path,changes)
        
        return docs

    def _delete_document(self, doc_id: str):
        """Internal method. Removes a document and cascades the deletion to its images."""
        cursor = self.conn.cursor()
        
        cursor.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        self.conn.commit()

    def _save_document(self, doc: Document):
        """Internal method. Saves a single Document object."""
        update_metadata_file(doc)
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
                doc.metadata.to_json() if doc.metadata else None,
                doc.last_modified, doc.error_msg if doc.error_msg else None
                )

        cursor.execute('''
            INSERT OR REPLACE INTO documents (doc_id, metadata, deskewed, needs_approval,
            approved, rejected, uploaded, path, metadata_file, metadata_file_type, metadata_json, last_modified, error_msg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',params_tuple )
        
        for image_id, image_data in doc.images.items():
            cursor.execute('''
                INSERT OR REPLACE INTO images (image_id, doc_id, sort_order, original_path, processed_path, changes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (image_id, doc.doc_id, image_data['order'], image_data['original'], image_data['processed'], json.dumps(image_data['changes'])))
        self.conn.commit()

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
            
        stored_hash = row['password_hash']
        salt = row['salt']
        role = row['role']
        
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