from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union

# --- Helper Function for Mutable Defaults ---

def _default_status_factory() -> Dict[str, bool]:
    """Returns a unique dictionary for the default status."""
    return {
        'discovered':False,
        'metadata':False,
        'deskewed':False,
        'needs_approval':True,
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
    error_msg: Optional[str] = None
    last_modified: Optional[str] = None
    status: Dict[str, bool] = field(default_factory=_default_status_factory)
    images: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    __repr__ = lambda self: f"Document(id={self.doc_id}, images={len(self.images)}, path={self.path})"

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

    def add_image(self, image_id: str, order: int, original_path: str, processed_path: str = None):
        """Adds or updates an image entry in the document."""
        self.images[image_id] = {
            "order": order,
            "original": str(original_path),
            "processed": str(processed_path) if processed_path else None
        }

    def to_dict(self) -> dict:
        """Converts the Document object to a dictionary for JSON serialization."""
        return {
            "doc_id": self.doc_id,
            "status": self.status,
            "images": self.images,
            "path": str(self.path) if self.path else None,
            "metadata_file": str(self.metadata_file) if self.metadata_file else None,
            "metadata_file_type": self.metadata_file_type,
            "last_modified": self.last_modified,
            "error_msg": self.error_msg
        }

    @classmethod
    def from_dict(cls, doc_id: str, data: dict) -> 'Document':
        """Creates a Document object from a dictionary."""
        return cls(
            doc_id=doc_id,
            status=data.get("status"),
            path=data.get("path"),
            metadata_file=data.get("metadata_file"),
            metadata_file_type=data.get("metadata_file_type"),
            last_modified=data.get("last_modified"),
            error_msg=data.get("error_msg"),
            images=data.get("images", {})
        )
