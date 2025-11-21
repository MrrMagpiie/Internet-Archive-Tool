import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout,QGridLayout,
    QPushButton, QLabel
)

from view.components.ActionCard import ActionCard
from view.components.ActionDashboard import ActionDashboard
from view.components.Page import Page

class SettingsPage(Page):
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
        title = "Settings Page"
        description = "will have tabs for various settings."
       
        # Title Section
        header = QLabel(f"<span id='stepTitle' style='font-size: 24pt; font-weight: 600;'>{title}</span>")
        header.setObjectName("dashHeader")
        subtitle = QLabel(f"<span id='stepDesc' style='font-size: 11pt;'>{description}</span>")
        subtitle.setObjectName("dashSubtitle")
        
        self.main_layout.addWidget(header)
        self.main_layout.addWidget(subtitle)
        self.main_layout.addSpacing(20)


