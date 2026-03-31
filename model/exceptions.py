class ArchiveError(Exception):
    """Base class for all exceptions in the archive program."""
    pass


# --- Document Process Errors --- 
class DocumentProcessError(ArchiveError):
    """Raised when an error occurs on a specific document."""
    
    def __init__(self, message: str, doc_id: str = "Undefined"):
        super().__init__(message)
        self.doc_id = doc_id

class DeskewError(DocumentProcessError):
    '''Raised when deskewing fails'''
    def __init__(self,in_dir,out_dir):
        self.in_file = in_dir
        self.out_file = out_dir 
        message = f"Error Deskewing image: {str(in_file)} to {str(out_file)}"
        super().__init__(message)

class ImageDiscoveryError(DocumentProcessError):
    '''Raised when image discovery fails'''
    pass
class DocumentCreationError(DocumentProcessError):
    '''Raised when document creation fails'''
    pass

class DocumentDeletionError(DocumentProcessError):
    '''Raised when document deletion fails'''
    pass

class TaskCancelledError(Exception):
    """Raised when a user intentionally aborts a background worker."""
    pass

class MetadataError(DocumentProcessError):
    """Raised when document metadata is malformed or missing."""
    pass

class PdfGenerationError(ArchiveError):
    """Raised when the PDF generation process fails."""
    pass 