from pathlib import Path

def get_image_list(directory) -> list:
    '''
    Returns list of paths for images in a directory
    '''
    image_formats = ['.tif', '.tiff', '.jpg', '.jpeg', '.png']
    path = Path(directory)
    return [p for p in path.iterdir() if p.suffix.lower() in image_formats]


def images_to_documents(image_list:list) -> dict:
    '''
    Takes list of paths and returns them as a dictionary organized by filename.
    requires image order to be annotated with a number at the end of the filename.
    '''
    documents = {}
    for file in image_list:
        file = Path(file)
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

