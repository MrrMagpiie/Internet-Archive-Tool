from PyQt6.QtWidgets import (
     QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy,
    QPushButton, QLabel,QSplitter,QListWidget, QStackedWidget,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt

from model.data.document import Document
from view.components import Page
from view.components import ImageLabel

from pathlib import Path

class DocumentImagePanel(QWidget):
    document_reviewed = pyqtSignal(str, str)

    def __init__(self,parent=None):
        super().__init__(parent)
        self.current_doc: Document = None
        self.images = []
        self.current_image_index = 0
        self._create_layout()
        

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
        self.display_image()

    def _go_to_next_image(self):
        if self.current_image_index < len(self.images) - 1:
            self.current_image_index += 1
            self.display_image()

    def _go_to_previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.display_image()

    def display_image(self):
        """Loads the image for the selected document at the current index."""
        
        if self.current_doc and self.images:
            image_key = self.images[self.current_image_index]
            image_path = self.current_doc.images[image_key]["processed"]
            if image_path == '':
                image_path = doc.images[image_key]['original']
            
            self.image_label.setPixmap(Path(image_path))
            print(f'displaying: {image_path}')
            # Update position label
            self.image_pos_label.setText(f"Page {self.current_image_index + 1} of {len(self.images)}")

  