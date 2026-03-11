from config import IA_CONFIG_PATH, DEV_MODE
import internetarchive as ia
import zipfile
import os
import json
from pathlib import Path
from wand.image import Image
import datetime
from model.exceptions import*

def update_metadata(doc,metadata):
    metadata_file = doc.metadata_file
    if metadata_file != None:
        with open(metadata_file,'w') as f:
            try:
                json.dump(metadata,f,indent=4)
                print('metadata updated')
            except Exception as e:
                print(f'metadata save error: {e}')

def load_metadata(doc):
    '''load metadata for current document'''
    metadata_file = doc.metadata_file
    if metadata_file != None:
        with open(metadata_file,'r') as f:
            metadata = json.load(f)
            return metadata

def uploadDocument(doc:Document,ticket:JobTicket):
        if not doc.metadata_file or not Path(doc.metadata_file).is_file():
            raise MetadataError(f"Error: Metadata file not found for {doc.doc_id}")

        zip_path = zip_doc(doc)
        pdf_path = create_pdf_from_tiffs(doc)
        upload(doc,[zip_path,pdf_path])

def setup(email: str, password: str):
        try:
            ia.configure(email,password=password,config_file=IA_CONFIG_PATH) 
        except Exception as e:
            raise e 

def zip_doc(doc):
    output_dir = Path(doc.path)
    zip_file_path = output_dir / f"{doc.doc_id}.zip"
    print(f"Creating zip file: {zip_file_path}")
    try:
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            print(doc.images)
            for image in doc.images.values():
                print(image)
                file_path = Path(image['processed'])
                # Add file to zip
                zipf.write(file_path, arcname=file_path.name)
        print("Zip file created successfully.")
        return str(zip_file_path)
    except Exception as e:
        raise e

def create_pdf_from_tiffs(doc):
    pdf_path = os.path.join(doc.path,f'{doc.doc_id}.pdf')
    try:
        with Image() as pdf:
            for tiff in doc.images.values():
                with Image(filename=tiff.get('processed')) as img:
                    pdf.sequence.append(img)
            
            # Save the combined PDF
            pdf.save(filename=pdf_path)
            print('pdf created Successfully.')
            return pdf_path
    except Exception as e:
        raise e

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

def upload(doc:Document, files:list,edit = False):
    metadata_dict = load_metadata(doc)
    identifier = metadata_dict.get('identifier')
    if not identifier:
        raise MetadataError(f"Error: 'identifier' not found in metadata for {doc.doc_id}")

    if DEV_MODE:
        print("DEV MODE ACTIVE: Redirecting upload to test_collection...")
        # Override the collection to the sandbox
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