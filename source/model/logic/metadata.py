from model.data.metadata import Metadata
from model.data.schema import DocumentSchema
from model.data.document import Document
import json

def update_metadata_file(doc:Document):
    if not doc.metadata:
        raise MetadataError(doc.doc_id,"No metadata found")

    if not doc.metadata_file or not doc.metadata_file.exists():
        doc.metadata_file = doc.path / 'metadata.json'
        
    data = doc.metadata.to_dict()

    try:
        doc.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(doc.metadata_file,'w') as f:
            json.dump(data,f,indent=4)

        return doc
    except Exception as e:
        raise f"Error saving metadata file for {doc.doc_id}: {e}"  

def get_metadata_from_file(doc:Document):
    if doc.metadata_file and doc.metadata_file.exists():
        with open(doc.metadata_file,'r') as f:
            return json.load(f)
    else:
        return None
