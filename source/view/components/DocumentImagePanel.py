import sys
from PyQt6.QtWidgets import (
     QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy,
    QPushButton, QLabel, QSplitter, QListWidget, QStackedWidget,
)
from PyQt6.QtGui import QPixmap, QColor, QImage
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QObject

from model.data import Document
from view.components.ImageLabel import ImageLabel
from view.components.InteractiveImageView import InteractiveImageViewer
from model.service.Signals import JobTicket
from pathlib import Path

class DocumentImagePanel(QWidget):
    document_reviewed = pyqtSignal(str, str)
    image_request = pyqtSignal(Path, QObject)

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.current_doc: Document = None
        self.images = []
        self.pending_requests = {}
        self.current_image_index = 0
        self.current_qimage = None
        self.show_original = False
        
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
        
        self.toggle_version_btn = QPushButton("View Original Image")
        self.toggle_version_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_version_btn.clicked.connect(self._toggle_image_version)
        
        toggle_layout = QHBoxLayout()
        toggle_layout.addStretch()
        toggle_layout.addWidget(self.toggle_version_btn)
        toggle_layout.addStretch()
        layout.addLayout(toggle_layout)

        self.prev_image_btn.clicked.connect(self._go_to_previous_image)
        self.next_image_btn.clicked.connect(self._go_to_next_image)
        
        self.changes_label = QLabel("Modifications: None")
        self.changes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.changes_label.setWordWrap(True)
        self.changes_label.setStyleSheet("color: #888888; font-size: 11px; margin-top: 5px;")
        layout.addWidget(self.changes_label)
        
    def _toggle_image_version(self):
        self.show_original = not self.show_original
        if self.show_original:
            self.toggle_version_btn.setText("View Processed Image")
        else:
            self.toggle_version_btn.setText("View Original Image")
        self.clear_cache()
        self.display_image()
        self._prefetch_neighbors()

    def show_new_document(self, doc: Document):
        self.current_doc = doc
        self.images = list(doc.images.keys())
        self.current_image_index = 0
        self.display_image()
        self._prefetch_neighbors()

    def _go_to_next_image(self):
        if self.current_image_index < len(self.images) - 1:
            self.current_image_index += 1
            self.display_image()
            self._prefetch_neighbors()

    def _go_to_previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.display_image()
            self._prefetch_neighbors()

    def display_image(self):
        self.image_label.set_image(self.loading_image)
        self.current_qimage = None
        if not self.images:
            self._update_changes_display()
            return
            
        self.image_pos_label.setText(f"Page {self.current_image_index + 1} of {len(self.images)}")
        self._update_changes_display()
        path = Path(self.get_image_path(self.current_image_index))
        self.fetch_image(path, self.current_image_index)

    def _update_changes_display(self):
        if not self.current_doc or not self.images:
            self.changes_label.setText("Modifications: None")
            return
            
        image_key = self.images[self.current_image_index]
        changes = self.current_doc.images[image_key].get('changes')
        
        if not changes:
            self.changes_label.setText("Modifications: None")
        else:
            if isinstance(changes, list):
                changes_text = ", ".join(str(c) for c in changes)
            elif isinstance(changes, dict):
                changes_text = ", ".join(f"{k}: {v}" for k, v in changes.items())
            else:
                changes_text = str(changes)
                
            self.changes_label.setText(f"Modifications: {changes_text}")
                
    def _prefetch_neighbors(self):
        if self.current_image_index > 0:
            path = Path(self.get_image_path(self.current_image_index - 1))
            self.fetch_image(path, self.current_image_index - 1)
        if self.current_image_index < len(self.images) - 1:
            path = Path(self.get_image_path(self.current_image_index + 1))
            self.fetch_image(path, self.current_image_index + 1)
    
    def get_image_path(self, index):
        if self.current_doc and self.images:
            image_key = self.images[index]
            if self.show_original:
                return self.current_doc.images[image_key]['original']
            else:
                image_path = self.current_doc.images[image_key].get("processed", "")
                if not image_path:
                    image_path = self.current_doc.images[image_key]['original']
                return image_path

    def fetch_image(self, path, indx):
        ticket = JobTicket()
        ticket.data.connect(self.image_return)
        ticket.error.connect(self.image_error)
        self.pending_requests[ticket.job_id] = (ticket, indx)

        self.image_request.emit(path, ticket)

    def clear_cache(self):
        for ticket, indx in self.pending_requests.values():
            ticket.cancel()
        self.pending_requests.clear()
        
    @pyqtSlot(object, str)
    def image_return(self, qimage, job_id):
        if job_id in self.pending_requests:
            ticket, indx = self.pending_requests.pop(job_id)
            if indx == self.current_image_index:
                self.image_label.set_image(qimage)
                self.current_qimage = qimage
    
    @pyqtSlot(Exception, str)
    def image_error(self, error, job_id):
        print(f"Failed to load image for job {job_id}: {error}")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.current_qimage and isinstance(self.current_qimage, QImage):
                popout_pixmap = QPixmap.fromImage(self.current_qimage)
                
                self.interactive_popout = InteractiveImageViewer()
                self.interactive_popout.set_pixmap(popout_pixmap)
                self.interactive_popout.show()