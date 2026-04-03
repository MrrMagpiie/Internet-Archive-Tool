from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout
)

class CountWidget(QWidget):
    """A simple wrapper for a label to display a count."""
    def __init__(self, label_text="Count:", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._count = 0
        
        self.prefix_lbl = QLabel(label_text)
        self.prefix_lbl.setObjectName("boldLabel")
        
        self.count_lbl = QLabel(str(self._count))
        self.count_lbl.setObjectName("highlightLabel")
        
        layout.addWidget(self.prefix_lbl)
        layout.addStretch()
        layout.addWidget(self.count_lbl)

    def set_count(self, value):
        self._count = value
        self.count_lbl.setText(str(self._count))

    def get_count(self):
        return self._count

    def increment(self,value: int =1):
        self.set_count(self.count + value)