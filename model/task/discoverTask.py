from PyQt6.QtCore import QRunnable,QObject,pyqtSignal,pyqtSlot
from model.logic.discover import *
from model.data.document import Document



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
                self.signals.data.emit(doc,signals.job_id)
            except Exception as e:
                self.signals.error.emit(f"Error processing command {command} for {signals.job_id}: {e}")