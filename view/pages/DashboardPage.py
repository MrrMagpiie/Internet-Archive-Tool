import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout,QGridLayout,
    QPushButton, QLabel
)

from view.components.ActionCard import ActionCard
from view.components.ActionDashboard import ActionDashboard
from view.components.Page import Page

class DashboardPage(Page):
    '''
    frontpage of application for choose actions
    '''

    def __init__(self,navigation_stack,parent=None):
        super().__init__(parent)
        self.stack = navigation_stack
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
        
        self.main_layout.addWidget(header)
        self.main_layout.addWidget(subtitle)
        self.main_layout.addSpacing(20)

        self.action_board = ActionDashboard(stack=self.stack)
        self._create_nav_cards()

        self.main_layout.addWidget(self.action_board)



    def _create_nav_cards(self):
        self.action_board.new_card(
            title = 'Single Document',
            icon_text = 'example icon',
            description = 'Process one document from start to finish',
            index = 1
        )
        self.action_board.new_card(
            title = 'Batch Steps',
            icon_text = 'example icon',
            description = 'Run indavidual steps for multiple documents at once',
            index = 2
        )
        self.action_board.new_card(
            title = 'settings',
            icon_text = 'example icon',
            description = 'Change settings for application and process',
            index = 2
        )