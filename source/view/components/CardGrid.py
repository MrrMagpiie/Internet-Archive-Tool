from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QObject
from PyQt6.QtGui import QPixmap
from pathlib import Path
from view.components import CenteredFlowLayout, ThumbnailCard, InteractiveImageViewer
from view.components.CountWidget import CountWidget
from model.logic.helpers import clear_layout
from model.service.Signals import JobTicket
from model.data.document import Document



class CardGrid(QWidget):
    image_request = pyqtSignal(Path, QObject)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("thumbnailGridContainer")
        
        self.all_cards = {}
        self._create_layout()
        self.pending_requests = {}
        
    def _create_layout(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        count_widget = CountWidget('Found:')
        self.discover_count = count_widget.count_lbl
        
        self.flow_layout = CenteredFlowLayout()
        self.flow_layout.setContentsMargins(20, 20, 20, 20)
        self.flow_layout.setSpacing(20)
        
        self.main_layout.addWidget(count_widget)
        self.main_layout.addLayout(self.flow_layout)

    def create_image_popout(self,page_id): 
            if page_id in self.all_cards:
                card = self.all_cards[page_id]
                self.interactive_popout = InteractiveImageViewer()
                self.interactive_popout.set_pixmap(card.image_view._original_image)
                self.interactive_popout.show()

    def add_card(self, pixmap, job_id):
        '''Add a card to the grid that creates an image popout when clicked'''
        
        if job_id not in self.pending_requests:
            return
            
        ticket, image_indx = self.pending_requests.pop(job_id)
        
        if image_indx not in self.all_cards:
            new_card = ThumbnailCard(image_indx, pixmap)
            self.flow_layout.addWidget(new_card)
            self.all_cards[image_indx] = new_card
            self.discover_count.setText(str(len(self.all_cards)))

    def clear_image_cards(self):
        self.all_cards.clear()
        clear_layout(self.flow_layout)

    def reset(self):
        self.clear_image_cards()
        for job_id, (ticket, task_type) in list(self.pending_requests.items()):
                ticket.cancel()
                self.pending_requests.pop(job_id)

    # --- Requests ---
    def fetch_images(self, document: Document):
        images = document.images
        for image in images.values():
            image_path = Path(image['original'])
            ticket = JobTicket()
            ticket.data.connect(self.image_return)
            ticket.error.connect(self.image_error)
            self.pending_requests[ticket.job_id] = (ticket, image['order'])
            self.image_request.emit(image_path, ticket)

    @pyqtSlot(object, str)
    def image_return(self, pixmap, job_id):
        self.add_card(pixmap, job_id)

    @pyqtSlot(Exception, str)
    def image_error(self, error, job_id):
        pass
