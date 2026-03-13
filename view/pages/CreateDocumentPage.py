import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit,
    QFileDialog, QProgressBar, QTableWidget,
    QComboBox, QLabel, QFormLayout, QFrame, QSplitter,
    QScrollArea, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, Qt

from view.components.Page import Page
from view.components.SchemaForm import SchemaForm, EditableSchemaForm
from view.components.CenteredFlowLayout import CenteredFlowLayout
from view.components.ThumbnailCard import ThumbnailCard
from view.components.InteractiveImageView import InteractiveImageViewer

from model.data.metadata import Metadata
from model.data.document import Document
from model.data.schema import DocumentSchema
from model.logic.helpers import clear_layout
from model.service.signals import JobTicket

import json
from config import RESOURCES_PATH

class CreateDocumentPage(Page):
    doc_ready = pyqtSignal(Document)
    discover_document = pyqtSignal(tuple, QObject)
    deskew_document = pyqtSignal(Document, QObject)
    image_request = pyqtSignal(Path, QObject)
    new_document = pyqtSignal(Document)
    next_stage = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.form = None
        self.main_layout = QVBoxLayout(self)
        self.all_cards = {}
        self.pending_requests = {}
        self.current_document = None
        
        self.create_layout()

    def create_layout(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # --- Left Side: Controls ---
        controls_widget = QWidget()
        controls_widget.setObjectName("createDocControlsPanel") # NEW: QSS Hook
        
        controls_layout = QVBoxLayout()
        # FIXED: Pack all controls to the top so they don't stretch weirdly
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignTop) 
        controls_layout.setSpacing(20)

        # Input Area
        input_widget = QWidget()
        input_layout = QVBoxLayout()
        input_layout.setContentsMargins(0,0,0,0)
        
        self.input_dir_field = QLineEdit()
        self.input_dir_field.setPlaceholderText("Select Document Folder...")
        input_layout.addWidget(self.input_dir_field)
        
        input_browse_btn = QPushButton("Browse...")
        input_browse_btn.clicked.connect(lambda: self.select_directory(self.input_dir_field))
        input_layout.addWidget(input_browse_btn)
        input_browse_btn.setObjectName("primaryActionBtn") # NEW: QSS Hook
        
        find_pages_btn = QPushButton("Find Pages")
        # NEW: Make the primary action pop
        find_pages_btn.setObjectName("primaryActionBtn") 
        find_pages_btn.clicked.connect(self.run_discover)
        input_layout.addWidget(find_pages_btn)
        
        input_widget.setLayout(input_layout)
    
        # Page Count Area    
        pages_widget = QWidget()
        pages_layout = QHBoxLayout()
        pages_layout.setContentsMargins(0,0,0,0)
        
        pages_lbl = QLabel('Pages Found:')
        pages_lbl.setObjectName("boldLabel") # NEW: QSS Hook
        
        self.pages_count = QLabel('0')
        self.pages_count.setObjectName("highlightLabel") # NEW: QSS Hook
        
        pages_layout.addWidget(pages_lbl)
        pages_layout.addStretch()
        pages_layout.addWidget(self.pages_count)
        pages_widget.setLayout(pages_layout)
        
        # Next Step Action
        nxt_step_btn = QPushButton('Deskew Images')
        nxt_step_btn.setObjectName("primaryActionBtn") # NEW: QSS Hook
        nxt_step_btn.clicked.connect(self._to_next_stage)

        controls_layout.addWidget(input_widget)
        
        # Draw a visual separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        controls_layout.addWidget(line)
        
        controls_layout.addWidget(pages_widget)
        controls_layout.addWidget(nxt_step_btn)

        controls_widget.setLayout(controls_layout)


        # --- Right Side: Flow Layout Grid ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setObjectName("thumbnailScrollArea") # NEW: QSS Hook
        
        self.grid_container = QWidget()
        self.grid_container.setObjectName("thumbnailGridContainer") # NEW: QSS Hook
        
        self.flow_layout = CenteredFlowLayout()
        self.flow_layout.setContentsMargins(20, 20, 20, 20)
        self.flow_layout.setSpacing(20)
        
        self.grid_container.setLayout(self.flow_layout)
        self.scroll_area.setWidget(self.grid_container)

        splitter.addWidget(controls_widget)
        splitter.addWidget(self.scroll_area)
        
        self.main_layout.addWidget(splitter)

    def set_current_document(self, document: Document):
        self.current_document = document
        self._reset()
        if document != None:
            self.input_dir_field.setText(str(document.path))
            self.fetch_images(document)

    # --- Discovery stuff --- 
    def select_directory(self, field):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory", options=QFileDialog.Option.DontUseNativeDialog)
        if dir_path:
            field.setText(dir_path)

    def get_paths(self):
        input_dir = self.input_dir_field.text().strip()
        output_dir = input_dir

        if not input_dir or not os.path.isdir(input_dir):
            return None, None
        return input_dir, output_dir

    def run_discover(self):
        input_dir, out_dir = self.get_paths()
        if input_dir and out_dir:
            data = (input_dir, out_dir)
            ticket = JobTicket()
            ticket.data.connect(self.discover_return)
            ticket.error.connect(self.doc_error)
            self.pending_requests[ticket.job_id] = (ticket, "discover")
            self.discover_document.emit(data, ticket)
        else:
            QMessageBox.information(self, 'Select Document Folder', 'Please choose the documents location')

    # --- Deskew Stuff ---
    def run_deskew(self):
        ticket = JobTicket()
        ticket.data.connect(self.deskew_return)
        ticket.error.connect(self.doc_error)
        self.pending_requests[ticket.job_id] = (ticket, 'deskew')
        self.deskew_document.emit(self.current_document, ticket)

    # --- Display stuff ---
    def fetch_images(self, document: Document):
        images = document.images
        for image in images.values():
            image_path = Path(image['original'])
            ticket = JobTicket()
            ticket.data.connect(self.image_return)
            ticket.error.connect(self.image_error)
            self.pending_requests[ticket.job_id] = (ticket, image['order'])
            self.image_request.emit(image_path, ticket)

    def add_card(self, pixmap, job_id):
        # Prevent KeyError if job_id was cancelled or already processed
        if job_id not in self.pending_requests:
            return
            
        ticket, image_indx = self.pending_requests.pop(job_id)
        
        if image_indx not in self.all_cards:
            new_card = ThumbnailCard(image_indx, pixmap)
            new_card.clicked.connect(self.handle_card_selection)
            self.flow_layout.addWidget(new_card)
            self.all_cards[image_indx] = new_card
            self.pages_count.setText(str(len(self.all_cards)))

    def clear_image_cards(self):
        self.all_cards.clear()
        clear_layout(self.flow_layout)

    def _reset(self):
        for job_id, (ticket, task_type) in list(self.pending_requests.items()):
            if task_type != 'deskew' and task_type != 'discover':
                ticket.cancel() 
                
        self.clear_image_cards()
        self.input_dir_field.setText('')
        self.pages_count.setText(str(len(self.all_cards)))

    # --- Next Page ---
    def _to_next_stage(self):
        print('next page clicked')
        if self.current_document:
            self.next_stage.emit()
            self.run_deskew()   
        else:
            QMessageBox.information(self, 'Find Pages', 'Please discover the document before deskewing')

    # --- Logic: Handle Selection ---
    def handle_card_selection(self, page_id):   
        print(f"User selected Page {page_id}")
        if page_id in self.all_cards:
            card = self.all_cards[page_id]
            self.create_image_popout(card.image_view._original_pixmap)

    def create_image_popout(self, pixmap):
        self.interactive_popout = InteractiveImageViewer()
        self.interactive_popout.set_pixmap(pixmap)
        self.interactive_popout.show()

    # --- Slots ---
    @pyqtSlot(Document)
    def db_update(self, doc):
        pass

    @pyqtSlot(Document, str)
    def discover_return(self, document, job_id):
        self.new_document.emit(document)
    
    @pyqtSlot(Document, str)
    def deskew_return(self, document, job_id):
        print('deskew success')

    @pyqtSlot(str, str)
    def doc_error(self, error_msg, job_id):
        print(error_msg)

    @pyqtSlot(object, str)
    def image_return(self, pixmap, job_id):
        self.add_card(pixmap, job_id)

    @pyqtSlot(str, str)
    def image_error(self, msg, job_id):
        pass