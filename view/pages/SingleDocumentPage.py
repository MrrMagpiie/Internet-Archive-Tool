
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit,
    QFileDialog, QProgressBar,QTableWidget,
    QComboBox,QLabel,QFormLayout
)
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from view.components.Page import Page
from view.components.SchemaForm import SchemaForm
import json
from config import RESOURCES_PATH

class SingleDocumentPage(Page):

    def __init__(self,parent):
        super().__init__(parent)
        self.create_layout()
        self._load_metadata_formats()

    def create_layout(self):
        main_layout = QVBoxLayout(self)
        
        input_layout = QHBoxLayout()
        self.input_dir_field = QLineEdit()
        input_layout.addWidget(self.input_dir_field)
        input_browse_btn = QPushButton("Select Document Folder")
        input_browse_btn.clicked.connect(lambda: self.select_directory(self.input_dir_field))
        input_layout.addWidget(input_browse_btn)
        main_layout.addLayout(input_layout)

        # add document type select
        metadata_layout = QVBoxLayout()
        self.doc_type_combo = QComboBox()
        self._load_metadata_formats()
        self.doc_type_combo.currentTextChanged.connect(self._on_select_format)
        metadata_layout.addWidget(self.doc_type_combo)
        
        # add metadata input table
        self.form = SchemaForm()
        metadata_layout.addWidget(self.form)
        main_layout.addLayout(metadata_layout)
        
        
        run_btn = QPushButton("Start Process")
        run_btn.clicked.connect(self.discoverButtonCallback)
        main_layout.addWidget(run_btn)


    # Discovery stuff
    def select_directory(self, field):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            field.setText(dir_path)

    def get_paths(self):
        input_dir = self.input_dir_field.text().strip()
        output_dir = input_dir + '/deskewed'

        if not input_dir or not os.path.isdir(input_dir):
            self.output_text.setPlainText("Please select a valid input directory!")
            return None, None
        
        return input_dir, output_dir

    def discoverButtonCallback(self):
        in_dir, out_dir = self.get_paths()
        if in_dir and out_dir:
            self.output_text.clear()
            self.progress_bar.setValue(0)
            self.discovery_signal.emit(in_dir, out_dir, self)



    # form stuff
    def _load_metadata_formats(self):
        with open(RESOURCES_PATH /'document_schema.json','r') as f:
            self.metadata_formats = json.load(f)
        self.doc_type_combo.clear()
        for key in self.metadata_formats.keys():
            self.doc_type_combo.addItem(key, self.metadata_formats[key])

    def _on_select_format(self,format):
        if format and format != '':
            fields = self.metadata_formats.get(format)
            self.form.new_form(fields)

    def clear_layout(self, layout):
        """Removes all widgets from a layout and schedules them for deletion."""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()


# --------------- Signals ---------------
    @pyqtSlot(str)
    def append_log(self, text):
        self.output_text.append(text.strip())

    @pyqtSlot(int)
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    @pyqtSlot()
    def task_finished(self):
        self.output_text.append("\nPipeline completed.\n")
        self.progress_bar.setValue(100)
        self.window().showNormal()
        self.window().raise_()