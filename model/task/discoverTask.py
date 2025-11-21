from PyQt6.QtCore import QRunnable,QObject,pyqtSignal,pyqtSlot
from model.logic.discover import *
from model.data.document import Document

class discoverSignals(QObject):
    image_error = pyqtSignal(Exception) # exception
    doc_error = pyqtSignal(object) # doc_id and exception
    document = pyqtSignal(Document)


class discoverTask(QRunnable):
    def __init__(self, signals, in_dir, out_dir = None):
        super().__init__()
        self.in_dir = Path(in_dir)
        self.out_dir = Path(out_dir)
        self.signals = signals

    def run(self):
        image_list = discover_images(self.in_dir)
        try:
            documents_dict = images_to_documents(image_list)
        except Exception as e:
            self.signals.image_error.emit(e)

        for doc_id in documents_dict.keys():
            try:
                doc = create_document(doc_id,documents_dict[doc_id])
                self.signals.document.emit(doc)
            except Exception as e:
                self.signals.error.emit(doc_id,e)