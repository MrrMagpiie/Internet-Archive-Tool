from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union
from model.data.metadata import Metadata
import json


# --- Helper Function for Mutable Defaults ---

def _default_status_factory() -> Dict[str, bool]:
    """Returns a unique dictionary for the default status."""
    return {
        'metadata':False,
        'deskewed':False,
        'needs_approval':False,
        'approved':False,
        'rejected':False,
        'uploaded':False
    }

# --- Document Dataclass ---

@dataclass
class Document:
    """
    Represents a document in the processing pipeline
    
    Fields that accept file paths are initialized as Optional[Path | str] to allow 
    loading from strings (e.g., from JSON) and are converted to Path objects in 
    __post_init__.
    """
    doc_id: str
    path: Optional[Union[Path, str]] = None
    metadata_file: Optional[Union[Path, str]] = None
    metadata_file_type: Optional[str] = None
    metadata: Optional[Metadata] = None
    error_msg: Optional[str] = None
    last_modified: Optional[str] = None
    status: Dict[str, bool] = field(default_factory=_default_status_factory)
    images: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    __repr__ = lambda self: f"Document(id={self.doc_id},status={self.status}, images={len(self.images)}, path={self.path})"

    def __post_init__(self):
        """
        Handles initialization steps not suited for simple field defaults:
        1. Converting path strings (if provided) to pathlib.Path objects.
        2. Setting the default last_modified timestamp if none was provided.
        """
        # 1. Path Conversion
        if isinstance(self.path, str):
            self.path = Path(self.path)
        
        if isinstance(self.metadata_file, str):
            self.metadata_file = Path(self.metadata_file)
        
        # 2. Last Modified Default
        if self.last_modified is None:
            self.last_modified = datetime.now(timezone.utc).isoformat()

    def add_image(self, image_id: str, order: int, original_path: str, processed_path: str = None,changes: list[Any] = None):
        """Adds or updates an image entry in the document."""
        self.images[image_id] = {
            "order": order,
            "original": str(original_path),
            "processed": str(processed_path) if processed_path else None,
            "changes": changes if changes else []
        }
        self.last_modified = datetime.now(timezone.utc).isoformat()

    def add_change(self,image_id,change):
        self.images[image_id]['changes'].append(change)
        self.last_modified = datetime.now(timezone.utc).isoformat()

    def add_metadata(self, metadata):
        if isinstance(metadata, Metadata):
            self.metadata = metadata
        elif isinstance(metadata, dict):
            self.metadata = Metadata.from_dict(metadata)
        elif isinstance(metadata, str):
            self.metadata = Metadata.from_json(metadata)
        else:
            return
        self.status['metadata'] = True
        self.last_modified = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        """Converts the Document object to a dictionary for JSON serialization."""
        return {
            "doc_id": self.doc_id,
            "status": self.status,
            "images": self.images,
            "path": str(self.path) if self.path else None,
            "metadata_file": str(self.metadata_file) if self.metadata_file else None,
            "metadata_file_type": self.metadata_file_type,
            "metadata_json": self.metadata.to_json() if self.metadata else None,
            "last_modified": self.last_modified,
            "error_msg": self.error_msg
        }

    def set_output_path(self,path):
        self.path = Path(path)
        for image_id,image in self.images.items():
            image['processed'] = str(self.path / image_id)
        self.last_modified = datetime.now(timezone.utc).isoformat()

    @classmethod
    def from_images(cls,doc_id,image_list) -> 'Document':
        '''
        Creates a Document instance from a list of images.
        '''
        Doc = Document(doc_id=doc_id)
        sorted_images = sorted(image_list, key=lambda x: int(x[2]))
        for file, image_id, order in sorted_images:
            Doc.add_image(
                        image_id=image_id,
                        order=order,
                        original_path=file,
                        processed_path= None
                    )
        return Doc

    @classmethod
    def from_db_row(cls, row) -> 'Document':
        """
        Creates a Document instance from a dictionary-like SQLite row.
        """
        status = { 
            'metadata': bool(row['metadata']),
            'deskewed': bool(row['deskewed']),
            'needs_approval': bool(row['needs_approval']),
            'approved': bool(row['approved']),
            'rejected': bool(row['rejected']),
            'uploaded': bool(row['uploaded'])
        }
        
        doc = cls(
            doc_id=row['doc_id'], 
            status=status, 
            path=row['path'], 
            metadata_file=row['metadata_file'], 
            metadata_file_type=row['metadata_file_type'],
            last_modified=row['last_modified'], 
            error_msg=row['error_msg']
        )

        if row['metadata_json']:
            doc.add_metadata(row['metadata_json'])

        return doc

from model.exceptions import MetadataError

def update_metadata_file(doc:'Document'):
    '''
    Takes a document and updates or creates its metadata file.
    '''
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

def get_metadata_from_file(doc:'Document'):
    '''
    Takes a document and returns the metadata stored in its metadata files.
    '''
    if doc.metadata_file and doc.metadata_file.exists():
        with open(doc.metadata_file,'r') as f:
            return json.load(f)
    else:
        return None