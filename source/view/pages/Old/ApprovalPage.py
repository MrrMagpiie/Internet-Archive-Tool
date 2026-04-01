from PyQt6.QtWidgets import (
     QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy,
    QPushButton, QLabel,QSplitter,QListWidget, QStackedWidget,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt

from view.components import Page
from view.components import ImageLabel

class ApprovalPage(Page):
    document_reviewed = pyqtSignal(str, str)

    def __init__(self,parent):
        super().__init__(parent)
        self.setWindowTitle("Review")
        self.db_data = {}
        self.current_doc_id = None
        self.current_image_index = 0
        self.current_image_keys = [] 
        self.create_layout()
        
    def create_layout(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # --- Left Panel ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_label = QLabel("Documents needing Approval:")
        left_layout.addWidget(left_label)
        self.doc_list = QListWidget()
        left_layout.addWidget(self.doc_list)
        splitter.addWidget(left_panel)
        
        # --- Right Panel ---
        self.right_panel = QWidget()
        right_panel_layout = QVBoxLayout(self.right_panel)
        self.stack = QStackedWidget()
        
        # Create a simple empty page for when nothing is selected
        self.empty_page = QLabel("Select a document from the list to begin review.")
        self.empty_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.image_page = self._create_image_page()

        self.stack.addWidget(self.empty_page)
        self.stack.addWidget(self.image_page)
        
        self.selected_label = QLabel('No document selected.')
        right_panel_layout.addWidget(self.selected_label)
        right_panel_layout.addWidget(self.stack)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([250, 600])

        # --- Connections ---
        self.doc_list.currentItemChanged.connect(self._on_doc_selected)

    def _create_image_page(self):
        """Creates the widget that contains the image viewer and navigation."""
        page = QWidget()
        layout = QVBoxLayout(page)
        
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

        
        review_layout = QHBoxLayout()
        approve_btn = QPushButton("Approve Document")
        reject_btn = QPushButton("Reject Document")
        review_layout.addStretch()
        review_layout.addWidget(reject_btn)
        review_layout.addWidget(approve_btn)
        review_layout.addStretch()

        layout.addLayout(image_layout)
        layout.addLayout(nav_layout)
        layout.addLayout(review_layout)

        prev_image_btn.clicked.connect(self._go_to_previous_image)
        next_image_btn.clicked.connect(self._go_to_next_image)
        approve_btn.clicked.connect(self._on_approve)
        reject_btn.clicked.connect(self._on_reject)
        
        return page

    @pyqtSlot(dict)
    def load_documents(self, db_data):
        """Receives the full manifest from the ProcessManager and populates the list."""
        self.doc_list.clear()
        self.db_data = db_data
        for doc_id, doc in db_data.items():
            if doc.status.get('metadata', True) and doc.status.get('deskewed',True):
                self.doc_list.addItem(doc_id)
        if self.current_doc_id:
            self.display_document

    def _on_doc_selected(self, current_item, previous_item):
        """When a document is selected, show the correct view in the stack."""
        if not current_item:
            self.current_doc_id = None
            self.selected_label.setText('No document selected.')
            self.stack.setCurrentWidget(self.empty_page) 
            return

        self.current_doc_id = current_item.text()
        self.current_image_index = 0
        
        doc = self.db_data.get(self.current_doc_id)
        if doc:
             self.current_image_keys = list(doc.images.keys())

        self.selected_label.setText(f'Reviewing: {self.current_doc_id}')
        self.stack.setCurrentWidget(self.image_page)
        self.display_document()

    def _go_to_next_image(self):
        if self.current_image_index < len(self.current_image_keys) - 1:
            self.current_image_index += 1
            self.display_document()

    def _go_to_previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.display_document()

    def display_document(self):
        """Loads the image for the selected document at the current index."""
        if not self.current_doc_id:
            return
            
        doc = self.db_data.get(self.current_doc_id)
        
        if doc and self.current_image_keys:
            image_key = self.current_image_keys[self.current_image_index]
            image_path = doc.images[image_key]["processed"]
            self.image_label.setPixmap(QPixmap(image_path))
            
            # Update position label
            total_images = len(self.current_image_keys)
            self.image_pos_label.setText(f"Page {self.current_image_index + 1} of {total_images}")

    def _on_approve(self):
        self._review_document("approved")
        
    def _on_reject(self):
        self._review_document("rejected")

    def _review_document(self, new_status: str):
        if not self.current_doc_id:
            return
            
        # Update the status in the local data model
        doc = self.db_data.get(self.current_doc_id)
        if doc:
            # Assuming you want to set the new status and clear 'needs_approval'
            doc.status['needs_approval'] = False
            doc.status[new_status] = True
            
            # Emit the entire updated document object to the manager
            self.document_reviewed.emit(doc.doc_id, new_status)
  