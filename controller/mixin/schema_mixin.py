import json
from PyQt6.QtCore import QThread, pyqtSlot, QObject
from pathlib import Path
from config import RESOURCES_PATH
from model.data.schema import DocumentSchema

schema_path = RESOURCES_PATH / 'document_schema.json'

class SchemaMixin:
    """Handles Schema creation/deletion logic."""   

    @pyqtSlot(DocumentSchema)
    def save_schema(self, schema):
        schema_dict = schema.to_dict()
        try:
            data = self.load_schema()

            data[schema_dict.get('schema_name')] = schema_dict
            
            with open(schema_path, 'w') as f: 
                json.dump(data, f, indent=4)
                    
        except Exception as e:
            self._handle_worker_error(f"Failed to save schema: {e}")

    @pyqtSlot(str)
    def delete_schema(self,schema_name):
        try:
            data= self.load_schema()
            if schema_name in data:
                del data[schema_name]
                
                with open(schema_path, 'w') as f: 
                    json.dump(data, f, indent=4)
            
        except Exception as e:
            self._handle_worker_error(f"Failed to delete schema: {e}")
            
    def load_schema(self):
        try:    
            if schema_path.exists():
                with open(schema_path, 'r') as f: 
                    data = json.load(f)
            else:
                data = {}
            return data
        except Exception as e:
            self._handle_worker_error(f"Failed to load schema file: {e}")