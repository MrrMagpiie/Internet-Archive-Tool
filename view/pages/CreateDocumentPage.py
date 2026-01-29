
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit,
    QFileDialog, QProgressBar,QTableWidget,
    QComboBox,QLabel,QFormLayout,QFrame,QSplitter,
    QScrollArea
)
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, Qt
from view.components.Page import Page
from view.components.SchemaForm import SchemaForm, EditableSchemaForm
from view.components.CenteredFlowLayout import CenteredFlowLayout
from view.components.ThumbnailCard import ThumbnailCard
from model.data.metadata import Metadata
from model.data.document import Document
from model.data.schema import DocumentSchema
from model.logic.helpers import *
import json
from config import RESOURCES_PATH

class CreateDocumentPage(Page):
    doc_ready = pyqtSignal(Document)
    discover_document = pyqtSignal(tuple,QObject)
    next_page = pyqtSignal()

    def __init__(self,parent):
        super().__init__(parent)
        self.form = None
        self.main_layout = QVBoxLayout(self)
        self.all_cards = []
        self.create_layout()

    def create_layout(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left Side
        controls_widget = QWidget()
        controls_layout = QVBoxLayout()

        # Input
        input_widget = QWidget()
        input_layout = QVBoxLayout()
        self.input_dir_field = QLineEdit()
        input_layout.addWidget(self.input_dir_field)
        input_browse_btn = QPushButton("Select Document Folder")
        input_browse_btn.clicked.connect(lambda: self.select_directory(self.input_dir_field))
        input_layout.addWidget(input_browse_btn)
        find_pages_btn = QPushButton("Find Pages")
        find_pages_btn.clicked.connect(self.run_discover)
        input_layout.addWidget(find_pages_btn)
        input_widget.setLayout(input_layout)
    
        # Page Count    
        pages_widget = QWidget()
        pages_layout = QHBoxLayout()
        pages_lbl = QLabel('Pages Found:')
        self.pages_count = QLabel('0')
        pages_layout.addWidget(pages_lbl)
        pages_layout.addWidget(self.pages_count)
        pages_widget.setLayout(pages_layout)
        
        nxt_step_btn = QPushButton('Add Metadata')

        controls_layout.addWidget(input_widget)
        controls_layout.addStretch()
        controls_layout.addWidget(pages_widget)
        controls_layout.addWidget(nxt_step_btn)

        controls_widget.setLayout(controls_layout)


        # Right Side
        # 1. The Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background-color: white;")
        
        # 2. The Container for Layout
        self.grid_container = QWidget()
        
        # 3. The Layout (Using the CenteredFlowLayout you added earlier)
        # Make sure CenteredFlowLayout is defined in your file!
        self.flow_layout = CenteredFlowLayout()
        self.flow_layout.setContentsMargins(20, 20, 20, 20)
        self.flow_layout.setSpacing(20)
        
        self.grid_container.setLayout(self.flow_layout)
        self.scroll_area.setWidget(self.grid_container)


        splitter.addWidget(controls_widget)
        splitter.addWidget(self.scroll_area)
        
        self.main_layout.addWidget(splitter)

    # Discovery stuff
    def select_directory(self, field):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            field.setText(dir_path)

    def get_paths(self):
        input_dir = self.input_dir_field.text().strip()
        output_dir = input_dir + '/deskewed'

        if not input_dir or not os.path.isdir(input_dir):
            return None, None
        print(input_dir,output_dir)
        return input_dir, output_dir

    def run_discover(self):
        input_dir, out_dir = self.get_paths()
        if input_dir and out_dir:
            data = (input_dir,out_dir)
            self.discover_document.emit(data,self)
        else:
            print('choose dir')

    def clear_layout(self, layout):
        """Removes all widgets from a layout and schedules them for deletion."""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()


        # --- Logic: Simulate Scanning ---

    def show_images(self, document: Document):
        images = document.images
        for image_path in images:
            full_path = os.path.join(document.path,image_path)
            print(full_path)

            next_num = len(self.all_cards) + 1
        
            new_card = ThumbnailCard(next_num, full_path)
            new_card.clicked.connect(self.handle_card_selection)
            self.flow_layout.addWidget(new_card)
            self.all_cards.append(new_card)
            self.pages_count.setText(str(next_num))
            self.handle_card_selection(str(next_num))


    # --- Logic: Handle Selection ---
    def handle_card_selection(self, page_id):
        print(f"User selected Page {page_id}")
        
        for card in self.all_cards:
            if str(card.page_number) == page_id:
                card.is_selected = True
            else:
                card.is_selected = False


    @pyqtSlot(Document)
    def db_update(self,doc):
        pass

    @pyqtSlot(Document)
    def doc_return(self,doc):
        self.doc_ready.emit(doc)

    @pyqtSlot(str)
    def doc_error(self,error_msg):
        pass

    @pyqtSlot()
    def _reset(self):
        clear_layout(self.main_layout)
        self.create_layout()
        self._on_select_format()

    @pyqtSlot(Document)
    def doc_return(self,document):
        print(' Create Document Page recived document')
        self.show_images(document)

    @pyqtSlot(str)
    def doc_error(self,error_msg):
        print(error_msg)


