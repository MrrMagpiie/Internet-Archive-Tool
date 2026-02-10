from pathlib import Path
from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPixmap   

from model.logic.loadImage import load_image

class FetchImageRequest(QObject):
    data = pyqtSignal(object) # QPixMap Return
    error = pyqtSignal(str) # Error Message Return


class ImageLoader(QObject):
    image = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, queue: Queue):
        super().__init__()
        self.queue = queue
        print('initImageLoader')

    @pyqtSlot()
    def run(self):
        """The main worker loop. This runs in the QThread."""
        
        try:
            print('Hello from Image Loader')
            while True:
                command, data = self.queue.get()
                print(f'running {command}')
                if command == 'shutdown':
                    break 

                try:
                    if command == 'single':
                        signals, image_path = data
                        if isinstance(image_path,Path):
                            pixmap = load_image(image_path)
                            signals.data.emit(pixmap)
                    if command == 'series':
                        signals, image_path_list = data
                        if isinstance(image_path_list,list):
                            pixmap_list = load_image_series(image_path_list)
                            signals.data.emit(pixmap_list)
                except Exception as e:
                    signals.error.emit((f"Error processing command {command}: {e}"))



        except Exception as e:
            self.error.emit(f"Worker-level error: {e}")