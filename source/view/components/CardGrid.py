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
        self.pending_popouts = {}
        self.current_document = None
        
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

    def create_image_popout(self, page_id): 
        if not self.current_document:
            return
            
        target_image = None
        for img in self.current_document.images.values():
            if str(img['order']) == str(page_id):
                target_image = img
                break
                
        if target_image:
            image_path = Path(target_image['original'])
            ticket = JobTicket()
            ticket.data.connect(self.popout_return)
            ticket.error.connect(self.image_error)
            self.pending_popouts[ticket.job_id] = ticket
            self.image_request.emit(image_path, ticket)

    def clear_image_cards(self):
        self.all_cards.clear()
        clear_layout(self.flow_layout)

    def reset(self):
        self.clear_image_cards()
        for job_id, (ticket, task_type) in list(self.pending_requests.items()):
            ticket.cancel()
        self.pending_requests.clear()
        
        for job_id, ticket in list(self.pending_popouts.items()):
            ticket.cancel()
        self.pending_popouts.clear()
        self.current_document = None

    # --- Requests ---
    def fetch_images(self, document: Document):
        self.current_document = document
        images = document.images
        sorted_images = sorted(images.values(), key=lambda x: int(x['order']))
        
        for image in sorted_images:
            image_indx = image['order']
            if image_indx not in self.all_cards:
                new_card = ThumbnailCard(image_indx)
                new_card.clicked.connect(self.create_image_popout)
                self.flow_layout.addWidget(new_card)
                self.all_cards[image_indx] = new_card
                
        self.discover_count.setText(str(len(self.all_cards)))

        for image in sorted_images:
            image_path = Path(image['original'])
            ticket = JobTicket()
            ticket.data.connect(self.image_return)
            ticket.error.connect(self.image_error)
            self.pending_requests[ticket.job_id] = (ticket, image['order'])
            self.image_request.emit(image_path, ticket)

    @pyqtSlot(object, str)
    def image_return(self, qimage, job_id):
        if job_id not in self.pending_requests:
            return
            
        ticket, image_indx = self.pending_requests.pop(job_id)
        
        if image_indx in self.all_cards:
            scaled_qimage = qimage.scaled(
                140, 180, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.all_cards[image_indx].set_image(scaled_qimage)

    @pyqtSlot(object, str)
    def popout_return(self, qimage, job_id):
        if job_id in self.pending_popouts:
            self.pending_popouts.pop(job_id)
            popout_pixmap = QPixmap.fromImage(qimage)
            self.interactive_popout = InteractiveImageViewer()
            self.interactive_popout.set_pixmap(popout_pixmap)
            self.interactive_popout.show()

    @pyqtSlot(Exception, str)
    def image_error(self, error, job_id):
        pass
