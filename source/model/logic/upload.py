from config import IA_CONFIG_PATH, DEV_MODE
import internetarchive as ia
import zipfile
import os
import json
from pathlib import Path
import datetime

from model.exceptions import *
from model.data.document import Document
from model.service.Signals import JobTicket

def setup(email: str, password: str):
        try:
            ia.configure(email,password=password,config_file=IA_CONFIG_PATH) 
        except Exception as e:
            raise e 

def build_zip(image_dict, output_path, progress_callback=None):
    """Creates a Zip file from a dict of images.
    if successfull returns output path. 
    progress_callback emits current step and total steps"""
    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            images = list(image_dict.values())
            total = len(images)
            for i, image in enumerate(images):
                file_path = Path(image['processed'])
                # Add file to zip
                zipf.write(file_path, arcname=file_path.name)
                if progress_callback:
                    progress_callback(i+1, total)
        return str(output_path)
    except Exception as e:
        raise

def build_pdf(image_dict, pdf_path, progress_callback=None):
    """Creates a PDF from a dict of images using wand.
    if successfull returns pdf_path.
    progress_callback emits current step and total steps"""
    try:
        from wand.image import Image
        with Image() as pdf:
            images = list(image_dict.values())
            total = len(images)
            for i, tiff in enumerate(images):
                with Image(filename=tiff.get('processed')) as img:
                    pdf.sequence.append(img)
                if progress_callback:
                    progress_callback(i+1, total)
            
            pdf.save(filename=str(pdf_path))
            return str(pdf_path)
    except Exception as e:
        raise

def build_IA_payload(doc_id, image_dict, output_dir, queue):
    """thread task to build the final upload files for IA"""
    def zip_progress(step, total):
        progress_pct = int((step / total) * 100)
        queue.put({"status": "zip_progress", "progress": progress_pct, "step": f"Generating PDF... {step}/{total}"})

    def pdf_progress(step,total):
        progress_pct = int((step / total) * 100)
        queue.put({"status": "pdf_progress", "progress": progress_pct, "step":f"Zipping files... {step}/{total}"})

    # ensure output path exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = output_dir / f'{doc_id}.pdf'
    zip_file_path = output_dir / f"{doc_id}.zip"
    
    try:
        build_zip(image_dict, zip_file_path, zip_progress)
        build_pdf(image_dict, pdf_path, pdf_progress)
        queue.put({"status": "success", "pdf_path": str(pdf_path), "zip_path": str(zip_file_path)})
    except Exception as e:
        queue.put({"status": "error", "error": str(e)})

from enum import Enum
class IdentifierStatus(Enum):
    FREE = 1
    ACTIVE = 2
    OFFLINE = 3

def check_identifier_status(identifier: str) -> IdentifierStatus:
    """Pings the IA database and returns the current state of the identifier."""
    item = ia.get_item(identifier)
    
    if not item.exists:
        return IdentifierStatus.FREE
        
    if item.is_dark:
        return IdentifierStatus.OFFLINE
        
    return IdentifierStatus.ACTIVE

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

def upload(metadata:dict, files:list,edit = False):
    identifier = metadata.get('identifier')
    if not identifier:
        raise MetadataError(f"Error: 'identifier' not found in metadata")

    print(f"Starting upload for item: {identifier}...")
    try:
        r = ia.upload(
            identifier=identifier,
            files=files,
            metadata=metadata,
            verbose=True
        )
        return r
    except Exception as e:
        raise e