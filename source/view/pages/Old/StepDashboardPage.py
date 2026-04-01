import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout,QGridLayout,
    QPushButton, QLabel,QStackedWidget,
    QHBoxLayout,QSpacerItem,QSizePolicy
)

from view.components.ActionCard import ActionCard
from view.components.ActionDashboard import ActionDashboard
from view.components.Page import Page

class StepDashboardPage(Page):
    '''
    frontpage of application for choose actions
    '''

    def __init__(self,parent=None):
        super().__init__(parent)
        self.stack = QStackedWidget()
        self. views = {}
        self._add_pages()
        self._create_layout()


    def _create_layout(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30) 
        title = "Image Processing Automation Dashboard"
        description = "Choose a specific task below or start a new end-to-end workflow."
       
        # Title Section
        header = QLabel(f"<span id='stepTitle' style='font-size: 24pt; font-weight: 600;'>{title}</span>")
        header.setObjectName("dashHeader")
        subtitle = QLabel(f"<span id='stepDesc' style='font-size: 11pt;'>{description}</span>")
        subtitle.setObjectName("dashSubtitle")
        
        # Global Back Button Setup
        self.back_button = QPushButton("Return to steps")
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        #self.back_button.setFont(QFont("Arial", 9))
        
        top_bar = QHBoxLayout()
        top_bar.addSpacing(15)
        top_bar.addWidget(self.back_button)
        top_bar.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.main_layout.addLayout(top_bar)
        self.main_layout.addWidget(self.stack)
    

    def _add_pages(self):
        # Dashbaord
        
        self.action_board = ActionDashboard(stack=self.stack)
        self.views['dashboard'] = self.action_board

        index = 1
        # Discovery Page
        discovery_page = self.parent.DiscoveryPage()
        self.views['discovery'] = discovery_page

        self.action_board.new_card(
            "Discover Files", "📝", 
            "Jump directly to the queue of processed images that require manual tagging and data entry.", 
            #'accent_metadata',
            index
        )
        index+=1
        
        # Deskew Page
        deskew_page = self.parent.DeskewPage()
        self.views['deskew'] = deskew_page
        self.action_board.new_card(
            "Deskew Files", "📝", 
            "Jump directly to the queue of processed images that require manual tagging and data entry.", 
            #'accent_metadata',
            index
        )
        index+=1
        
        # Metadata Page
        metadata_page = self.parent.MetadataPage()
        self.views['metadata'] = metadata_page
        self.action_board.new_card(
            "Add Metadata", "📝", 
            "Jump directly to the queue of processed images that require manual tagging and data entry.", 
            #'accent_metadata',
            index
        )
        index+=1

        #Approval Page
        approval_page = self.parent.ApprovalPage()
        self.views['approval_page'] = approval_page
        self.action_board.new_card(
            "Approve Files", "✅", 
            "Jump directly to the queue of processed images that require manual tagging and data entry.", 
            #'accent_metadata',
            index
        )
        index+=1

        # Upload Page
        upload_page = self.parent.UploadPage()
        self.views['upload'] = upload_page
        self.action_board.new_card(
            "Upload Files", "📤", 
            "Jump directly to the queue of processed images that require manual tagging and data entry.", 
            #'accent_metadata',
            index
        )
        
        index+=1
        
        self.action_board._rearrange_cards(1)
        for view in self.views.values():
            self.stack.addWidget(view)
        
        self.stack.setCurrentIndex(0)