import sqlite3
import hashlib
import secrets
import json
from abc import ABC, abstractmethod
from pathlib import Path
from model.data.document import Document, update_metadata_file

VALID_FILTERS = {
    'doc_id', 'metadata', 'deskewed', 'needs_approval', 'approved', 
    'rejected', 'uploaded', 'path', 'metadata_file', 'metadata_file_type', 
    'metadata_json', 'last_modified', 'error_msg'
}

class AbstractDatabaseProvider(ABC):
    """Abstract base class outlining the required methods for any database implementation."""
    
    @abstractmethod
    def connect(self): pass
    @abstractmethod
    def disconnect(self): pass
    @abstractmethod
    def cancel_current_query(self): pass
    @abstractmethod
    def load_documents(self, filters: dict = None) -> dict[str, Document]: pass
    @abstractmethod
    def save_document(self, doc: Document): pass
    @abstractmethod
    def delete_document(self, doc_id: str): pass
    @abstractmethod
    def verify_login(self, username, password) -> tuple[bool, str | None]: pass
    @abstractmethod
    def create_user(self, username, password, role) -> tuple[bool, str]: pass
    @abstractmethod
    def get_users(self) -> list[dict]: pass
    @abstractmethod
    def delete_user(self, user_id: str) -> tuple[bool, str]: pass
    @abstractmethod
    def has_admin(self) -> bool: pass
    @abstractmethod
    def has_admin_sync(self) -> bool: pass


class SQLiteProvider(AbstractDatabaseProvider):
    """Concrete SQLite implementation of the AbstractDatabaseProvider."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._create_tables()

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def cancel_current_query(self):
        if self.conn:
            self.conn.interrupt()

    def _create_tables(self):
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
        cursor.execute("PRAGMA table_info(documents)")
        existing_columns = {col[1] for col in cursor.fetchall()}
        if 'metadata_json' not in existing_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN metadata_json TEXT")
        self.conn.commit()

    def create_user(self, username, password, role) -> tuple[bool, str]:
        cursor = self.conn.cursor()
        salt = secrets.token_hex(16)
        hashed_pw = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, salt, role)
                VALUES (?, ?, ?, ?)
            ''', (username, hashed_pw, salt, role))
            self.conn.commit()
            return True, "User created successfully."
        except sqlite3.IntegrityError:
            self.conn.rollback()
            return False, f"The username '{username}' is already taken."
        except Exception as e:
            self.conn.rollback()
            return False, f"Database error: {str(e)}"

    def get_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id, username, role FROM users")
        return [dict(row) for row in cursor.fetchall()]

    def delete_user(self, user_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            if self.has_admin():
                self.conn.commit()
                return True, "User deleted."
            else:
                raise ValueError("Cannot delete last admin account.")
        except Exception as e:
            self.conn.rollback()
            raise

    def load_documents(self, filters: dict = None) -> dict[str, Document]:
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
                    docs[doc_id].add_image(image_id, order, orig_path, proc_path, changes)
        return docs

    def delete_document(self, doc_id: str):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        self.conn.commit()

    def save_document(self, doc: Document):
        update_metadata_file(doc)
        cursor = self.conn.cursor()
        status = doc.status
        params_tuple = (
                doc.doc_id, int(status.get('metadata', 0)), int(status.get('deskewed', 0)), 
                int(status.get('needs_approval', 0)), int(status.get('approved', 0)), 
                int(status.get('rejected', 0)), int(status.get('uploaded', 0)), 
                str(doc.path), str(doc.metadata_file) if doc.metadata_file else None, 
                str(doc.metadata_file_type) if doc.metadata_file_type else None,
                doc.metadata.to_json() if doc.metadata else None,
                doc.last_modified, doc.error_msg if doc.error_msg else None
        )
        cursor.execute('''
            INSERT OR REPLACE INTO documents (doc_id, metadata, deskewed, needs_approval,
            approved, rejected, uploaded, path, metadata_file, metadata_file_type, metadata_json, last_modified, error_msg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', params_tuple )
        
        for image_id, image_data in doc.images.items():
            cursor.execute('''
                INSERT OR REPLACE INTO images (image_id, doc_id, sort_order, original_path, processed_path, changes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (image_id, doc.doc_id, image_data['order'], image_data['original'], image_data['processed'], json.dumps(image_data['changes'])))
        self.conn.commit()

    def verify_login(self, username, plaintext_password) -> tuple[bool, str | None]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT password_hash, salt, role FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if not row:
            return False, None
        stored_hash = row['password_hash']
        salt = row['salt']
        role = row['role']
        test_hash = hashlib.pbkdf2_hmac('sha256', plaintext_password.encode('utf-8'), salt.encode('utf-8'), 100000).hex()
        if test_hash == stored_hash:
            return True, role
        return False, None

    def has_admin(self) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1")
        return cursor.fetchone() is not None

    def has_admin_sync(self) -> bool:
        if not self.db_path.exists():
            return False
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if not cursor.fetchone():
                    return False
                cursor.execute("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1")
                return cursor.fetchone() is not None
        except sqlite3.Error:
            return False