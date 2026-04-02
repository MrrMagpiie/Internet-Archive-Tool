from config import IA_CONFIG_PATH, DEV_MODE
import internetarchive as ia
import zipfile
import os
import json
from pathlib import Path
import datetime

from model.exceptions import*
from model.logic.metadata import update_metadata_file, get_metadata_from_file
from model.data.document import Document
from model.service.Signals import JobTicket

def setup(email: str, password: str):
        try:
            ia.configure(email,password=password,config_file=IA_CONFIG_PATH) 
        except Exception as e:
            raise e 

def uploadDocument(doc:Document,ticket:JobTicket):
        if not doc.metadata_file or not Path(doc.metadata_file).is_file():
            raise MetadataError(doc.doc_id,f"Metadata file not found")

        zip_path = zip_doc(doc)
        pdf_path = create_pdf_from_tiffs(doc)
        upload(doc,[zip_path,pdf_path])

def zip_doc(doc, ticket=None, base_progress=0, max_progress=100):
    output_dir = Path(doc.path)
    zip_file_path = output_dir / f"{doc.doc_id}.zip"
    print(f"Creating zip file: {zip_file_path}")
    try:
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            images = list(doc.images.values())
            total = len(images)
            for i, image in enumerate(images):
                file_path = Path(image['processed'])
                # Add file to zip
                zipf.write(file_path, arcname=file_path.name)
                if ticket:
                    current_prog = base_progress + int(((i + 1) / total) * (max_progress - base_progress))
                    ticket.update_progress(current_prog, f"Zipping files... {i+1}/{total}")
        print("Zip file created successfully.")
        return str(zip_file_path)
    except Exception as e:
        raise e

def pdf_from_tiffs(images_dict, pdf_path, queue):
    """The isolated Laborer. Do not pass the full Document object, just what it needs!"""
    try:
        from wand.image import Image
        with Image() as pdf:
            images = list(images_dict.values())
            total = len(images)
            for i, tiff in enumerate(images):
                with Image(filename=tiff.get('processed')) as img:
                    pdf.sequence.append(img)
                progress_pct = int(((i + 1) / total) * 100)
                queue.put({"status": "progress", "progress": progress_pct, "step": f"Generating PDF... {i+1}/{total}"})
            
            pdf.save(filename=str(pdf_path))
            queue.put({"status": "success", "pdf_path": str(pdf_path)})
    except Exception as e:
        queue.put({"status": "error", "error": str(e)})

from enum import Enum
class IdentifierStatus(Enum):
    FREE = 1
    ACTIVE = 2
    OFFLINE = 3

def _check_identifier_status(identifier: str) -> IdentifierStatus:
    """Pings the IA database and returns the current state of the identifier."""
    item = ia.get_item(identifier)
    
    if not item.exists:
        return IdentifierStatus.FREE
        
    if item.is_dark:
        return IdentifierStatus.OFFLINE
        
    return IdentifierStatus.ACTIVE

def check_identifier_status(identifier: str) -> IdentifierStatus:
    return IdentifierStatus.FREE

def get_unique_identifier(base_identifier:str) -> str:
    """
    Pings the Internet Archive for collisions.
    If taken, appends the current digitization date (e.g., _20260309).
    """
    current_id = base_identifier
    
    if not ia.get_item(current_id).exists:
        return current_id
        
    # 2. If base_id is taken, append today's date
    date_str = datetime.date.today().strftime("%Y%m%d")
    current_id = f"{base_identifier}_{date_str}"
    
    # 3. Fallback: add a simple counter to the date to guarantee safety.
    counter = 1
    while ia.get_item(current_id).exists:
        current_id = f"{base_identifier}_{date_str}_{counter}"
        counter += 1
        
    return current_id

def update_metadata(doc:Document, metadata:dict):
    doc.add_metadata(metadata)
    update_metadata_file(doc)

def upload(doc:Document, files:list,edit = False):
    metadata_dict = doc.metadata.to_dict()
    identifier = metadata_dict.get('identifier')
    if not identifier:
        raise MetadataError(f"Error: 'identifier' not found in metadata for {doc.doc_id}")

    if DEV_MODE:
        print("DEV MODE ACTIVE: Redirecting upload to test_collection...")
        metadata_dict['collection'] = 'test_collection'
        identifier = f"{identifier}_TEST"
        metadata_dict['identifier'] = identifier
        update_metadata(doc,metadata_dict)

    print(f"Starting upload for item: {identifier}...")
    try:
        r = ia.upload(
            identifier=identifier,
            files=files,
            metadata=metadata_dict,
            verbose=True
        )
        return r
    except Exception as e:
        raise e