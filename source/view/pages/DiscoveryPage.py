import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QFileDialog,
    QComboBox, QLabel, QFrame, QSplitter,
    QScrollArea, QMessageBox
)
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, Qt

from view.components import (
    Page,CenteredFlowLayout,ThumbnailCard,InteractiveImageViewer,AnimatedToggle,CardGrid,CountWidget
)

from model.data.document import Document, update_metadata_file
from model.data.schema import DocumentSchema
from model.logic.helpers import clear_layout, load_metadata_formats
from model.service.Signals import JobTicket
import json
class DocumentExpandableCard(QFrame):
    def __init__(self, document: Document, parent=None):
        super().__init__(parent)
        self.document = document
        self.setObjectName("documentCard") 
        
        # Give the card a nice border and background (hooks into your stylesheet)
        self.setStyleSheet("""
            QFrame#documentCard {
                border: 1px solid #444;
                border-radius: 6px;
                background-color: rgba(255, 255, 255, 0.02);
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # 1. The Header Button
        self.header_btn = QPushButton()
        self.header_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)
        self.header_btn.clicked.connect(self.toggle_expand)
        
        self.content_widget = QWidget()
        self.content_widget.setVisible(False)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(30, 0, 10, 15)
        self.content_layout.setSpacing(5)
        
        # Add a subtle line to separate header from content
        self.content_layout.addWidget(self._create_separator())

        # 3. Populate the images inside the content area
        sorted_images = sorted(
            self.document.images.items(), 
            key=lambda x: int(x[1].get('order', 0))
        )
        
        for img_id, img_data in sorted_images:
            page_num = img_data.get('order', 'N/A')
            lbl = QLabel(f"📄 Page {page_num}: {img_id}")
            lbl.setStyleSheet("color: #aaaaaa; font-size: 12px;")
            self.content_layout.addWidget(lbl)
            
        self.layout.addWidget(self.header_btn)
        self.layout.addWidget(self.content_widget)
        
        # Set the initial text
        self._update_header_text(is_expanded=False)

    def _create_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("border-top: 1px solid #333; margin-bottom: 5px;")
        return line

    def toggle_expand(self):
        """Switches the visibility of the content area."""
        is_visible = self.content_widget.isVisible()
        self.content_widget.setVisible(not is_visible)
        self._update_header_text(is_expanded=not is_visible)
        
    def _update_header_text(self, is_expanded: bool):
        arrow = "▼" if is_expanded else "▶"
        self.header_btn.setText(
            f"{arrow}   {self.document.doc_id}   ({len(self.document.images)} pages)"
        )

class BatchDocumentList(QWidget):
    """A container to hold all the DocumentAccordions."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list = []
        self._create_layout()
        

    def _create_layout(self):
        self.count_widget = CountWidget('Found:')
        self.main_layout.addWidget(self.count_widget)
        self.setObjectName("thumbnailGridContainer")

        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)
        self.main_layout.addLayout(self.layout)


    def add_document(self, document: Document):
        self.list.append(document)
        card = DocumentExpandableCard(document)
        self.layout.addWidget(card)
        self.count_widget.set_count(len(self.list))

    def get_list(self):
        return self.list

    def clear_list(self):
        clear_layout(self.layout)
        self.list.clear()
        self.count_widget.set_count(0)

class DiscoverControls(QWidget):
    run_discover = pyqtSignal(Path)
    run_deskew = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("createDocControlsPanel") 
        self._create_layout()
        self.populate_formats_combo()

    def _create_layout(self):
        self.controls_layout = QVBoxLayout(self)
        self.controls_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.controls_layout.setSpacing(20)
        
        self.input_dir_field = QLineEdit()
        self.input_dir_field.setPlaceholderText("Select Document Folder...")
        self.controls_layout.addWidget(self.input_dir_field)
        
        input_browse_btn = QPushButton("Browse...")
        input_browse_btn.clicked.connect(self.select_directory)
        self.controls_layout.addWidget(input_browse_btn)
        input_browse_btn.setObjectName("primaryActionBtn")
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.controls_layout.addWidget(line)

        find_metadata_layout = QHBoxLayout()
        self.find_metadata_toggle = AnimatedToggle()
        self.find_metadata_toggle.toggled.connect(self.metadata_toggled)
        find_metadata_label = QLabel('Auto Create Metadata')

        find_metadata_layout.addWidget(self.find_metadata_toggle)
        find_metadata_layout.addWidget(find_metadata_label)
        self.controls_layout.addLayout(find_metadata_layout)

        self.doc_type_combo = QComboBox()
        self.doc_type_combo.setVisible(False)
        self.doc_type_combo.setObjectName("formComboBox")
        self.controls_layout.addWidget(self.doc_type_combo)

        self.find_btn = QPushButton("Discover")
        self.find_btn.setObjectName("primaryActionBtn") 
        self.find_btn.clicked.connect(self.discover_callback)
        self.controls_layout.addWidget(self.find_btn)
        
        self.deskew_btn = QPushButton('Deskew Images')
        self.deskew_btn.setObjectName("primaryActionBtn")
        self.deskew_btn.setVisible(False)
        self.deskew_btn.clicked.connect(self.run_deskew.emit)
        self.controls_layout.addWidget(self.deskew_btn)
       
    def select_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory", options=QFileDialog.Option.DontUseNativeDialog)
        if dir_path:
            self.input_dir_field.setText(dir_path)

    def discover_callback(self):
        input_dir = self.input_dir_field.text().strip()
        if input_dir and os.path.isdir(input_dir):
            self.run_discover.emit(Path(input_dir))
            self.deskew_btn.setVisible(True)
        else:
            QMessageBox.information(self, 'Select Document Folder', 'Please choose the documents location')

    def populate_formats_combo(self):
        self.metadata_formats = load_metadata_formats()
        self.doc_type_combo.clear()
        for key,value in self.metadata_formats.items():
            if value['filename_template'] != '': 
                self.doc_type_combo.addItem(value['schema_name'], key)

    def metadata_toggled(self):
        self.doc_type_combo.setVisible(self.find_metadata_toggle.isChecked())
        if self.find_metadata_toggle.isChecked():
            self.find_btn.setText('Find + Create Metadata')
        else:
            self.find_btn.setText('Find')

    def get_metadata_type(self):
        return self.doc_type_combo.currentData()

    def reset(self):
        self.input_dir_field.setText('')
        #self.discover_count.setText('0')

class DiscoverPage(Page):
    doc_ready = pyqtSignal(Document)
    discover_document = pyqtSignal(Path, QObject)
    deskew_document = pyqtSignal(Document, QObject)
    save_metadata = pyqtSignal(tuple, JobTicket)
    new_document = pyqtSignal(Document)
    next_stage = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.form = None
        self.pending_requests = {}
        self.current_document = None
        self._create_layout()

    def _create_layout(self):
        self.main_layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # --- Left Side: Controls ---
        self.controls_widget = DiscoverControls()
        self.controls_widget.run_discover.connect(self.run_discover)
        self.controls_widget.run_deskew.connect(self.run_deskew)
        
        # --- Right Side: Flow Layout Grid ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        splitter.addWidget(self.controls_widget)
        splitter.addWidget(self.scroll_area)
        
        self.main_layout.addWidget(splitter)

    def set_current_document(self, document: Document):
        self._reset()
        self.current_document = document
        if document != None:
            self.controls_widget.input_dir_field.setText(str(document.path))
            self.controls_widget.deskew_btn.setVisible(True)

    def run_metadata(self,document:Document):
        filename = Path(document.path).stem
        metadata_type = self.controls_widget.get_metadata_type()
        schema = DocumentSchema.from_dict(load_metadata_formats()[metadata_type])
        metadata = schema.generate_metadata_from_name(filename)
        
        document.metadata_file_type = metadata_type
        document.add_metadata(metadata)

    def run_discover(self, input_dir:Path):
        data = input_dir
        ticket = JobTicket()
        ticket.data.connect(self.discover_return)
        ticket.error.connect(self.doc_error)
        self.pending_requests[ticket.job_id] = (ticket, "discover")
        self.discover_document.emit(data, ticket)

    def run_deskew(self,document:Document = None):
        if  not document:
            document = self.current_document
        ticket = JobTicket()
        ticket.data.connect(self.deskew_return)
        ticket.error.connect(self.doc_error)
        self.pending_requests[ticket.job_id] = (ticket, 'deskew')
        self.deskew_document.emit(document, ticket)
    
    def _to_next_stage(self):
            self.next_stage.emit()

    def _reset(self):
        for job_id, (ticket, task_type) in list(self.pending_requests.items()):
            if task_type != 'deskew' and task_type != 'discover':
                ticket.cancel()
                self.pending_requests.pop(job_id)

        self.controls_widget.reset()
        self.current_document = None
            
    # --- Slots ---
    @pyqtSlot(Document, str)
    def deskew_return(self, document, job_id):
        print('deskew success')

    @pyqtSlot(Exception, str)
    def doc_error(self, error, job_id):
        print(error)

    @pyqtSlot(Document, str)
    def discover_return(self, document, job_id):
        pass

class BatchDiscoveryPage(DiscoverPage):
    batch_request = pyqtSignal(Path, QObject)

    def __init__(self, parent):
        super().__init__(parent)

    def _create_layout(self):
        super()._create_layout()
        self.scroll_area.setObjectName("batchScrollArea")
        
        self.document_list = BatchDocumentList()
        self.scroll_area.setWidget(self.document_list)

    def run_discover(self, input_dir:Path):
        data = input_dir
        ticket = JobTicket()
        ticket.data.connect(self.discover_return)
        ticket.error.connect(self.doc_error)
        self.pending_requests[ticket.job_id] = (ticket, "discover")
        self.batch_request.emit(data, ticket)

    def run_deskew(self):
        for document in self.document_list.get_list():
            super().run_deskew(document)
        self._complete()

    def _reset(self):
        """Ensure the list clears when the user runs a new discovery."""
        super()._reset()
        if hasattr(self, 'document_list'):
            self.document_list.clear_list()

    def _complete(self):
        self.next_stage.emit()

    @pyqtSlot(Document, str)
    def discover_return(self, document, job_id):
        self.document_list.add_document(document)
        if self.controls_widget.find_metadata_toggle.isChecked():
            self.run_metadata(document)

class SingleDiscoveryPage(DiscoverPage):
    image_request = pyqtSignal(Path, QObject)
    def __init__(self,parent):
        super().__init__(parent)

    def _create_layout(self):
        super()._create_layout()
        self.scroll_area.setObjectName("thumbnailScrollArea")

        self.thumbnail_grid = CardGrid()
        self.thumbnail_grid.image_request.connect(self.image_request)
        self.scroll_area.setWidget(self.thumbnail_grid)

    def _reset(self):
        super()._reset()
        self.thumbnail_grid.clear_image_cards()

    def set_current_document(self, document: Document):
        super().set_current_document(document)
        if document != None:
            self.thumbnail_grid.fetch_images(document)

    def _to_next_stage():
        if self.current_document:
            self.next_stage.emit()
            self.run_deskew()
        else:
            QMessageBox.information(self, 'Find Pages', 'Please discover the document before deskewing')

    @pyqtSlot(Document, str)
    def discover_return(self, document, job_id):
        self.new_document.emit(document)
        if self.controls_widget.find_metadata_toggle.isChecked():
            self.run_metadata(document)