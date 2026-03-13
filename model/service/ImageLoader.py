from pathlib import Path
from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from model.logic.loadImage import load_image

class FetchImageRequest(QObject):
    data = pyqtSignal(object) # QPixMap Return
    error = pyqtSignal(str) # Error Message Return


class ImageLoader(QObject):
    success = pyqtSignal(str)#Job_id
    error = pyqtSignal(str,str)# error_msg, Job_id

    def __init__(self, queue: Queue):
        super().__init__()
        self.queue = queue
        print('init ImageLoader')

    @pyqtSlot()
    def run(self):
        """The main worker loop. This runs in the QThread."""
        
        try:
            print('Image Loader queue running')
            while True:
                command,signals, data = self.queue.get()
                if command == 'shutdown':
                    break 
                if signals.is_cancelled():
                            continue
                print(f'running {command}')
                

                try:
                    match command:
                        case 'single':
                            image_path = data
                            if isinstance(image_path,Path):
                                pixmap = load_image(image_path)
                                if not signals.is_cancelled():
                                    signals.data.emit(pixmap,signals.job_id)
                                    self.success.emit(signals.job_id)
                        case 'series':
                            image_path_list = data
                            if isinstance(image_path_list,list):
                                pixmap_list = load_image_series(image_path_list)
                                if not signals.is_cancelled():
                                    signals.data.emit(pixmap_list,signals.job_id)
                                    self.success.emit(signals.job_id)

                except Exception as e:
                    err_msg = f"Error processing command {command} for {signals.job_id}: {e}"
                    signals.error.emit(err_msg,signals.job_id)
                    self.error.emit(err_msg,signals.job_id)

        except Exception as e:
            self.error.emit(f"Image Worker-level error:  {e}",'')