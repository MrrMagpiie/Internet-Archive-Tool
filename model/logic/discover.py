from pathlib import Path
from model.data.document import Document
from config import DEFAULT_OUTPUT_DIR

def discover_images(directory) -> list:
    path = Path(directory)
    return list(path.glob("*.tif"))

def images_to_documents(image_list) -> dict:
    documents = {}
    for file in image_list:
        try:
            parts = file.stem.split()
            order = "001"
            if len(parts) > 1:
                order = "".join(char for char in parts.pop() if char.isdigit())
            doc_id = "_".join(parts)
            image_id = file.name

            if doc_id in documents.keys():
                documents[doc_id].append((file,image_id,order))
            else:
                documents[doc_id] = [(file,image_id,order)]
    
        except Exception as e:
            raise
    return documents
    
def create_document(doc_id,images):
    Doc = Document(doc_id=doc_id)
    Doc.path = DEFAULT_OUTPUT_DIR / doc_id
    print(Doc.path)
    for file, image_id, order in images:
        Doc.add_image(
                    image_id=image_id,
                    order=order,
                    original_path=file,
                    processed_path= Doc.path / image_id
                )
    return Doc

def batch_create_documents(documents_dict):
    documents = []
    for doc_id in documents_dict.keys():
        doc = create_document(doc_id,documents_dict[doc_id])
        documents.append(doc)
    return documents