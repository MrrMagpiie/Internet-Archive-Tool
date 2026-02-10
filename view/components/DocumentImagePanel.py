from PyQt6.QtWidgets import (
     QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy,
    QPushButton, QLabel,QSplitter,QListWidget, QStackedWidget,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt,QObject

from model.data.document import Document
from view.components import Page
from view.components import ImageLabel

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
        self.to_load = []
        self.current_image_index = 0
        self._create_layout()
        self.first_load = True
        

    def _create_layout(self):
        """Creates the widget that contains the image viewer and navigation."""
        layout = QVBoxLayout(self)
        
        image_layout = QHBoxLayout()
        self.image_label = ImageLabel()

        image_layout.addStretch() 
        image_layout.addWidget(self.image_label)
        image_layout.addStretch() 

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
        self.image_label.setPixmap(pixmap)
        # Update position label
        self.image_pos_label.setText(f"Page {self.current_image_index + 1} of {len(self.images)}")

    def fetch_image_rel_current(self,indx_diff):
        indx = self.current_image_index + indx_diff
        if indx >=0 and indx < len(self.images):
            path = Path(self.get_image_path(indx))
            if indx not in self.pixmap_cache:
                self.pixmap_cache[indx] = ''
                self.to_load.append(indx)
                self.image_request.emit(path,self)

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

    def cache_image(self,pixmap):
        indx = self.to_load.pop(0)
        self.pixmap_cache[indx] = pixmap
        if self.first_load:
            self.first_load = False
            self.display_image()

    @pyqtSlot(object)
    def image_return(self, pixmap):
        self.cache_image(pixmap)
    
    @pyqtSlot(str)
    def image_error(self,msg):
        pass
