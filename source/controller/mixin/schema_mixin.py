import json
from PyQt6.QtCore import QThread, pyqtSlot, QObject
from pathlib import Path
from config import DOCUMENT_SCHEMA_PATH
from model.data.schema import DocumentSchema

class SchemaMixin:
    """Handles Schema creation/deletion logic."""   

    @pyqtSlot(DocumentSchema)
    def save_schema(self, schema):
        schema_dict = schema.to_dict()
        try:
            data = self.load_schema()

            data[schema_dict.get('schema_name')] = schema_dict
            
            with open(DOCUMENT_SCHEMA_PATH, 'w') as f: 
                json.dump(data, f, indent=4)
                    
        except Exception as e:
            self._handle_worker_error(f"Failed to save schema: {e}")

    @pyqtSlot(str)
    def delete_schema(self,schema_name):
        try:
            data= self.load_schema()
            if schema_name in data:
                del data[schema_name]
                
                with open(DOCUMENT_SCHEMA_PATH, 'w') as f: 
                    json.dump(data, f, indent=4)
            
        except Exception as e:
            self._handle_worker_error(f"Failed to delete schema: {e}")
            
    def load_schema(self):
        try:    
            if DOCUMENT_SCHEMA_PATH.exists():
                with open(DOCUMENT_SCHEMA_PATH, 'r') as f: 
                    data = json.load(f)
            else:
                data = {}
            return data
        except Exception as e:
            self._handle_worker_error(f"Failed to load schema file: {e}")