from PyQt6.QtWidgets import (
     QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy,
    QPushButton, QLabel,QSplitter,QListWidget, QStackedWidget,
)
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt,QObject

from model.data.document import Document
from view.components import Page
from view.components import ImageLabel
from model.service.signals import JobTicket
from pathlib import Path

class DocumentImagePanel(QWidget):
    document_reviewed = pyqtSignal(str, str)
    image_request = pyqtSignal(Path,QObject)

    def __init__(self,parent=None):
        super().__init__()
        self.parent = parent
        self.current_doc: Document = None
        self.images = []
        self.pixmap_cache = {}
        self.pending_requests = {}
        self.current_image_index = 0
        self._create_loading_placeholder()
        self._create_layout()

        
    def _create_loading_placeholder(self) -> QPixmap:
        """Creates a simple gray placeholder image. You can replace this with a real image file."""
        pixmap = QPixmap(800, 1000)
        pixmap.fill(QColor(220, 220, 220)) # Light gray
        self.loading_pixmap = pixmap


    def _create_layout(self):
        """Creates the widget that contains the image viewer and navigation."""
        layout = QVBoxLayout(self)
        
        image_layout = QHBoxLayout()
        self.image_label = ImageLabel()

        image_layout.addWidget(self.image_label)

        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        nav_layout = QHBoxLayout()
        prev_image_btn = QPushButton("< Previous Page")
        next_image_btn = QPushButton("Next Page >")
        self.image_pos_label = QLabel("Page 1 of 1") 
        
        nav_layout.addWidget(prev_image_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.image_pos_label)
        nav_layout.addStretch()
        nav_layout.addWidget(next_image_btn)


        layout.addLayout(image_layout)
        layout.addLayout(nav_layout)

        prev_image_btn.clicked.connect(self._go_to_previous_image)
        next_image_btn.clicked.connect(self._go_to_next_image)
        

    def show_new_document(self, doc: Document):
        self.current_doc = doc
        self.images = list(doc.images.keys())
        self.current_image_index = 0
        self.fetch_image_rel_current(0)
        self._prefetch_neighbors()

    def _go_to_next_image(self):
        if self.current_image_index < len(self.images) - 1:
            self.current_image_index += 1
            self.display_image()
            self.fetch_image_rel_current(1)

    def _go_to_previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.display_image()
            self.fetch_image_rel_current(-1)

    def display_image(self):
        indx = self.current_image_index
        pixmap = self.pixmap_cache[indx]
        if isinstance(pixmap, QPixmap):
            self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setPixmap(self.loading_pixmap)
        # Update position label
        self.image_pos_label.setText(f"Page {self.current_image_index + 1} of {len(self.images)}")

    def fetch_image_rel_current(self,indx_diff):
        indx = self.current_image_index + indx_diff
        if indx >=0 and indx < len(self.images):
            path = Path(self.get_image_path(indx))
            if indx not in self.pixmap_cache:
                self.pixmap_cache[indx] = ''
                self.fetch_image(path,indx)
                
    def _prefetch_neighbors(self):
        self.fetch_image_rel_current(-1)
        self.fetch_image_rel_current(1)
    
    def get_image_path(self,index):
        if self.current_doc and self.images:
            image_key = self.images[index]
            image_path = self.current_doc.images[image_key]["processed"]
            if image_path == '':
                image_path = doc.images[image_key]['original']
            return image_path

    def cache_image(self,pixmap,job_id):
        indx = self.pending_requests.pop(job_id)
        self.pixmap_cache[indx] = pixmap
        if indx == self.current_image_index:
            self.display_image()

    def fetch_image(self,path,indx):
        ticket = JobTicket()
        ticket.data.connect(self.image_return)
        ticket.error.connect(self.image_error)
        self.pending_requests[ticket.job_id] = indx

        self.image_request.emit(path,ticket)

    def clear_cache(self):
        self.pixmap_cache.clear()
        
    @pyqtSlot(object,str)
    def image_return(self, pixmap,job_id):
        self.cache_image(pixmap,job_id)
    
    @pyqtSlot(str,str)
    def image_error(self,msg,job_id):
        pass
