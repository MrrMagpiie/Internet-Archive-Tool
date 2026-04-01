
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout,
    QPushButton, QTextEdit, QProgressBar,
    
)

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from view.components import Page

class DeskewPage(Page):
    deskew_signal = pyqtSignal(QObject)
    cancel_signal = pyqtSignal()
    def __init__(self, parent):
        super().__init__(parent)
        self.create_layout()

    def create_layout(self):
        layout = QVBoxLayout(self)

        run_btn = QPushButton("Deskew Images")
        run_btn.clicked.connect(self.deskewButtonCallback)
        layout.addWidget(run_btn)
        stop_btn = QPushButton("Stop Deskew")
        stop_btn.clicked.connect(self.stopButtonCallback)
        layout.addWidget(stop_btn)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

    
    def deskewButtonCallback(self):
        self.deskew_signal.emit(self)
    def stopButtonCallback(self):
        self.cancel_signal.emit()

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
