from config import RESOURCES_PATH
import internetarchive as ia
import zipfile
import os
import json
from pathlib import Path
from wand.image import Image

def upload(doc:Document):
        if not doc.metadata_file or not Path(doc.metadata_file).is_file():
            raise Exception(f"Error: Metadata file not found for {doc.doc_id}")

        zip_path = zip_doc(doc)
        pdf_path = create_pdf_from_tiffs(doc)

        with open(doc.metadata_file, 'r') as f:
            metadata_dict = json.load(f)

        identifier = metadata_dict.get('identifier')
        if not identifier:
            raise Exception(f"Error: 'identifier' not found in metadata for {doc.doc_id}")

        print(f"Starting upload for item: {identifier}...")
        try:
            r = ia.upload(
                identifier=identifier,
                files=[zip_path,pdf_path],
                metadata=metadata_dict,
                verbose=true
            )

        except Exception as e:
            raise e

def setup(self,email: str, password: str):
        target_dir = os.path.join(RESOURCES_PATH,'/ia.ini')

        try:
            ia.configure(email,password=password,config_file=target_dir) 
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
            for tiff_path in doc.images.values():
                with Image(filename=tiff_path) as img:
                    pdf.sequence.append(img)
            
            # Save the combined PDF
            pdf.save(filename=pdf_path)
            return pdf_path
    except Exception as e:
        raise e