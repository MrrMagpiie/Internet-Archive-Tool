import sys
from PyQt6.QtWidgets import (
     QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy,
    QPushButton, QLabel, QSplitter, QListWidget, QStackedWidget,
)
from PyQt6.QtGui import QPixmap, QColor, QImage
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QObject

from model.data import Document
from view.components import ImageLabel
from view.components.InteractiveImageView import InteractiveImageViewer
from model.service.signals import JobTicket
from pathlib import Path

class DocumentImagePanel(QWidget):
    document_reviewed = pyqtSignal(str, str)
    image_request = pyqtSignal(Path, QObject)

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.current_doc: Document = None
        self.images = []
        self.image_cache = {} 
        self.pending_requests = {}
        self.current_image_index = 0
        
        self._create_loading_placeholder()
        self._create_layout()
      
    def _create_loading_placeholder(self):
        """Creates a placeholder QImage to hold the layout dimensions."""
        image = QImage(800, 1000, QImage.Format.Format_RGB32)
        image.fill(QColor(220, 220, 220)) # Light gray fallback
        self.loading_image = image

    def _create_layout(self):
        """Creates the widget that contains the image viewer and navigation."""
        layout = QVBoxLayout(self)
        
        image_layout = QHBoxLayout()
        self.image_label = ImageLabel()
        
        self.image_label.setObjectName("documentImageLabel")
        image_layout.addWidget(self.image_label)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        nav_layout = QHBoxLayout()
        
        self.prev_image_btn = QPushButton("< Previous Page")
        self.prev_image_btn.setObjectName("imageNavButton") 
        
        self.next_image_btn = QPushButton("Next Page >")
        self.next_image_btn.setObjectName("imageNavButton") 
        
        self.image_pos_label = QLabel("Page 1 of 1") 
        self.image_pos_label.setObjectName("imagePosLabel") 
        
        nav_layout.addWidget(self.prev_image_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.image_pos_label)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_image_btn)

        layout.addLayout(image_layout)
        layout.addLayout(nav_layout)

        self.prev_image_btn.clicked.connect(self._go_to_previous_image)
        self.next_image_btn.clicked.connect(self._go_to_next_image)
        
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
        cached_item = self.image_cache.get(indx)

        if isinstance(cached_item, QImage):
            self.image_label.set_image(cached_item)
        else:
            self.image_label.set_image(self.loading_image)
            
        self.image_pos_label.setText(f"Page {self.current_image_index + 1} of {len(self.images)}")

    def fetch_image_rel_current(self, indx_diff):
        indx = self.current_image_index + indx_diff
        if indx >=0 and indx < len(self.images):
            path = Path(self.get_image_path(indx))
            if indx not in self.image_cache:
                self.image_cache[indx] = ''
                self.fetch_image(path, indx)
                
    def _prefetch_neighbors(self):
        self.fetch_image_rel_current(-1)
        self.fetch_image_rel_current(1)
    
    def get_image_path(self, index):
        if self.current_doc and self.images:
            image_key = self.images[index]
            image_path = self.current_doc.images[image_key]["processed"]
            if image_path == '':
                image_path = self.current_doc.images[image_key]['original']
            return image_path

    def _cleanup_cache(self):
        """
        Garbage Collection: Deletes QImages from RAM if they are more 
        than 3 pages away from the user's current view.
        """
        keys_to_remove = []
        for indx in self.image_cache.keys():
            if abs(indx - self.current_image_index) > 3:
                keys_to_remove.append(indx)
                
        for indx in keys_to_remove:
            del self.image_cache[indx]

    def cache_image(self, qimage, job_id):
        if job_id in self.pending_requests:
            ticket, indx = self.pending_requests.pop(job_id)
            self.image_cache[indx] = qimage
            self._cleanup_cache()
            
            if indx == self.current_image_index:
                self.display_image()

    def fetch_image(self, path, indx):
        ticket = JobTicket()
        ticket.data.connect(self.image_return)
        ticket.error.connect(self.image_error)
        self.pending_requests[ticket.job_id] = (ticket, indx)

        self.image_request.emit(path, ticket)

    def clear_cache(self):
        for ticket, indx in self.pending_requests.values():
            ticket.cancel()
        self.image_cache.clear()
        self.display_image()
        
    @pyqtSlot(object, str)
    def image_return(self, qimage, job_id):
        self.cache_image(qimage, job_id)
    
    @pyqtSlot(Exception, str)
    def image_error(self, error, job_id):
        print(f"Failed to load image for job {job_id}: {error}")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            cached_item = self.image_cache.get(self.current_image_index)
            
            if isinstance(cached_item, QImage):
                popout_pixmap = QPixmap.fromImage(cached_item)
                
                self.interactive_popout = InteractiveImageViewer()
                self.interactive_popout.set_pixmap(popout_pixmap)
                self.interactive_popout.show()