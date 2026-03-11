class ArchiveError(Exception):
    """Base class for all exceptions in the archive program."""
    pass

class MetadataError(ArchiveError):
    """Raised when document metadata is malformed or missing required fields."""
    pass

