import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QGridLayout, QStackedWidget,
    QPushButton, QLabel, QFrame, QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QSize,QPropertyAnimation, QEasingCurve,pyqtSignal,pyqtSlot

from view.components.ClickableFrame import ClickableFrame
from model.data.document import Document
from view.components.StyleManager import STYLE_OFF, STYLE_ON

class DocumentCardSignals(QWidget):
    ''' signal object for a document card

    update_status: takes a dict for new statuses, only needs the statuses that need to change    
    '''
    update_status = pyqtSignal(dict)

class DocumentCard(QWidget):
    def __init__(self,document: Document, parent: QWidget | None = None):
        super().__init__(parent)
        self.doc_id = document.doc_id
        self.status = document.status

        self.is_expanded = False
        self.summary_widgets = []
        self.indicators = {}

        self._create_layout()
        self._add_indicators()
        self._add_content()

    def _create_layout(self):
        self.header_frame = ClickableFrame()

        self.header_layout = QVBoxLayout()
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(5)

        doc_id_label = QLabel(self.doc_id)
        self.header_layout.addWidget(doc_id_label)

        self.indicator_layout = QFrame()
        self.header_layout.addWidget(self.indicator_layout)
        
        self.header_frame.setLayout(self.header_layout)

        self.content_area = QFrame()
        self.content_area.setStyleSheet("""
            QFrame { 
                background-color: #fafafa; 
                border: 1px solid #ccc;
                border-top: none; 
                border-radius: 0 0 4px 4px; /* Round bottom corners */
                margin-top: -1px; /* Overlap header border */
            }
        """)
        self.content_area.setMaximumHeight(0)
        self.content_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(5)
        self.content_area.setLayout(self.content_layout)

        self.animation = QPropertyAnimation(self.content_area, b"maximumHeight")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.header_frame)
        main_layout.addWidget(self.content_area)
        self.setLayout(main_layout)

        # --- Connections ---
        # Connect the header's custom 'clicked' signal to our toggle slot
        self.header_frame.clicked.connect(self.toggle)

    def toggle(self):
        """Handles the expand/collapse animation and summary visibility."""
        
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            # --- EXPAND ---
            self.header_frame.set_open_style(is_open=True)
            
            # --- NEW: Hide summary widgets ---
            for w in self.summary_widgets:
                w.setVisible(False)
            
            self.animation.setStartValue(0)
            full_height = self.content_layout.sizeHint().height()
            self.animation.setEndValue(full_height)
        else:
            # --- COLLAPSE ---
            self.header_frame.set_open_style(is_open=False)
            
            # --- NEW: Show summary widgets ---
            for w in self.summary_widgets:
                w.setVisible(True)
                
            self.animation.setStartValue(self.content_area.height())
            self.animation.setEndValue(0)
            
        self.animation.start()

    def _add_header_widget(self, widget: QWidget):
        """
        Adds a widget to the summary area.
        This widget will be hidden when the card is expanded.
        """
        self.header_layout.addWidget(widget)
        # --- NEW: Add to our tracking list ---
        self.summary_widgets.append(widget)

    def _add_detail_widget(self, widget: QWidget):
        """Adds a widget to the (collapsible) detail area."""
        self.content_layout.addWidget(widget)

    def _add_indicators(self):
        
        for item in self.status.keys():
            header_indicator = StatusIndicator()
            header_indicator.set_state(self.status.get(item))

            detail_indicator = StatusIndicator()
            detail_indicator.set_state(self.status.get(item))
            
            self.indicators[item] = {'detail':detail_indicator,'header':header_indicator}

    def _add_content(self):
        header_indicator_layout = QHBoxLayout()
        header_indicator_frame = QFrame()

        for item in self.indicators.keys():

            detail_indicator = self.indicators[item].get('detail')
            detail_indicator_layout = QHBoxLayout()
            detail_indicator_frame = QFrame()

            detail_indicator_layout.addWidget(detail_indicator)
            detail_indicator_layout.addWidget(QLabel(item))
            detail_indicator_layout.addWidget(QLabel(str(detail_indicator._is_on)))
            detail_indicator_frame.setLayout(detail_indicator_layout)
            self._add_detail_widget(detail_indicator_frame)

            header_indicator = self.indicators[item].get('header')
            header_indicator_layout.addWidget(header_indicator)
        header_indicator_frame.setLayout(header_indicator_layout)
        self._add_header_widget(header_indicator_frame)

    @pyqtSlot(dict)
    def update_status(self,status):
        for key in status.keys():
            self.status[key] = status[key]
        for indicator in self.indicators.keys():
            self.indicators[indicator]['detail'].set_state(status.get(indicator))
            self.indicators[indicator]['header'].set_state(status.get(indicator))

class StatusIndicator(QLabel):
    """A simple, circular on/off indicator."""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set a fixed size for the circle
        self.setFixedSize(QSize(20, 20))
        
        # Start in the "off" state
        self._is_on = False
        self.setStyleSheet(STYLE_OFF)

    def set_state(self, is_on: bool):
        """Toggles the indicator's state."""
        self._is_on = is_on
        if self._is_on:
            self.setStyleSheet(STYLE_ON)
        else:
            self.setStyleSheet(STYLE_OFF)

    def toggle(self):
        """Convenience method to flip the state."""
        self.set_state(not self._is_on)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    card = DocumentCard(doc_id='doc_id',status={'on':True,'off':False})
    test_button = QPushButton()
    test_button.clicked.connect(lambda:card.update_status(status={'on':False,'off':True}))

    window_layout = QVBoxLayout()
    window_layout.addWidget(card)
    window_layout.addWidget(test_button)
    window.setLayout(window_layout)
    window.show()
    sys.exit(app.exec())