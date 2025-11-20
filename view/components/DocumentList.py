import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QGridLayout, QStackedWidget,
    QPushButton, QLabel, QFrame, QSizePolicy, QSpacerItem,
)
from PyQt6.QtCore import Qt, QSize

from view.components.DocumentCard import DocumentCard, DocumentCardSignals
from model.data.document import Document


class DocumentList(QWidget):
    def __init__():
        super().__init__()
        self.documents = []



    def _create_layout():
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        
        scroll_content_widget = QWidget()

        self.scroll_layout = QVBoxLayout()
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll_content_widget.setLayout(self.scroll_layout)

        scroll_area.setWidget(scroll_content_widget)

    def _add_content(self):
        self.clear_content()
        for doc in self.documents:
                card = self.create_service_card(f"Service {i+1}: {name}", color, status)
                self.scroll_layout.addWidget(card)
        self.scroll_layout.addStretch()

    def clear_content(self):    
        """
        Removes all widgets and layouts from a given layout.
        """
        while self.scroll_layout.count() > 0:
            item = self.scroll_layout.takeAt(0)
            
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def add_card(doc:Document):
        ''' adds a new card for given document
        '''

        pass



