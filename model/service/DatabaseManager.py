import sqlite3
from pathlib import Path
from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from model.data.document import Document

class DatabaseSignal(QObject):
    data = pyqtSignal(str,object)# data return 
    error = pyqtSignal(str)# error msg
    prog = pyqtSignal(int)# progress update
    



class DatabaseManager(QObject):
    """
    A QObject worker that manages all database interactions
    in a separate thread.
    """
    success = pyqtSignal()
    save_document = pyqtSignal(object)
    error = pyqtSignal(str) #error_msg
    prog = pyqtSignal(int)# progress

    def __init__(self, db_path: Path, queue: Queue):
        super().__init__()
        self.db_path = db_path
        self.queue = queue
        self.conn = None 
        print('initDB')

    @pyqtSlot()
    def run(self):
        """The main worker loop. This runs in the QThread."""
        try:
            print('Hello from the Database Manager')
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(self.db_path)
            self._create_tables()

            while True:
                command, data = self.queue.get()
                print(f'db running {command}')
                if command == 'shutdown':
                    break 

                try:
                    if command == 'load_documents':
                        signals, filter_data = data
                        docs = self._load_documents(filter_data)
                        signals.data.emit(command,docs)
                    
                    elif command == 'load_single_document':
                        signals, doc_id = data
                        doc = self._load_single_document(doc_id)
                        signals.data.emit(command,doc)

                    elif command == 'save_document':
                        signals, document = data
                        self._save_document(document)
                        signals.data.emit(command,document)
                        self.save_document.emit(document)
                
                except Exception as e:
                    signals.error.emit(f"Error processing command {command}: {e}")
                    self.error.emit((f"Error processing command {command}: {e}"))

        except Exception as e:
            self.error.emit(f"Worker-level error: {e}")
        finally:
            if self.conn:
                self.conn.close()

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