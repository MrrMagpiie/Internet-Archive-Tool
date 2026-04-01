
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QFileDialog, QProgressBar,
)
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from view.components import Page

class DiscoveryPage(Page):
    discovery_signal = pyqtSignal(str, str, QObject)

    def __init__(self,parent):
        super().__init__(parent)
        self.create_layout()

    def create_layout(self):
        layout = QVBoxLayout(self)
        # Input/Output fields... (omitted for brevity, same as original)
        input_layout = QHBoxLayout()
        self.input_dir_field = QLineEdit()
        input_layout.addWidget(self.input_dir_field)
        input_browse_btn = QPushButton("Select Input Directory")
        input_browse_btn.clicked.connect(lambda: self.select_directory(self.input_dir_field))
        input_layout.addWidget(input_browse_btn)
        layout.addLayout(input_layout)

        output_layout = QHBoxLayout()
        self.output_dir_field = QLineEdit()
        output_layout.addWidget(self.output_dir_field)
        output_browse_btn = QPushButton("Select Output Directory")
        output_browse_btn.clicked.connect(lambda: self.select_directory(self.output_dir_field))
        output_layout.addWidget(output_browse_btn)
        layout.addLayout(output_layout)

        run_btn = QPushButton("Discover files")
        run_btn.clicked.connect(self.discoverButtonCallback)
        layout.addWidget(run_btn)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

    def select_directory(self, field):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            field.setText(dir_path)

    def get_paths(self):
        input_dir = self.input_dir_field.text().strip()
        output_dir = self.output_dir_field.text().strip()

        if not input_dir or not os.path.isdir(input_dir):
            self.output_text.setPlainText("Please select a valid input directory!")
            return None, None
        if not output_dir or not os.path.isdir(output_dir):
            pass
        return input_dir, output_dir

    def discoverButtonCallback(self):
        in_dir, out_dir = self.get_paths()
        if in_dir and out_dir:
            self.output_text.clear()
            self.progress_bar.setValue(0)
            self.discovery_signal.emit(in_dir, out_dir, self)

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