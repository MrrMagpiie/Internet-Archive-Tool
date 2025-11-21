from model.data.metadata import Metadata
from model.data.schema import DocumentSchema
from model.data.document import Document
import json

def add_metadata_to_document(doc:Document,metadata:Metadata,metadata_file_type):
    doc.metadata_file = doc.path / 'metadata.json'
    doc.metadata_file_type = metadata_file_type
    
    data = metadata.to_dict()
    try:
        with open(doc.metadata_file,'w') as f:
            json.dump(data,f,indent=4)

        return doc
    except Exception as e:
        raise f"Error saving metadata file for {doc.doc_id}: {e}"  
