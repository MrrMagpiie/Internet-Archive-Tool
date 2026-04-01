import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QGridLayout, QStackedWidget,
    QPushButton, QLabel, QFrame, QSizePolicy, QSpacerItem,
)
from PyQt6.QtCore import Qt, QSize,QTimer
from PyQt6.QtGui import QIcon, QFont, QFontDatabase

class ActionCard(QFrame):
    def __init__(self,title,icon_text,description):
        super().__init__()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) 
        self.setObjectName("actionCardFrame") 

        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.icon_label = QLabel(icon_text)
        self.icon_label.setObjectName("cardIconLabel")
        layout.addWidget(self.icon_label)
        

        text_layout = QVBoxLayout(self)
        # Title: Font size determined dynamically
        self.title_label = QLabel(f"<span id='cardTitleText'>{title}</span>") 
        self.title_label.setObjectName("cardTitleLabel")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding) 
        text_layout.addWidget(self.title_label)
        layout.addSpacing(3)

        # Description: Font size determined dynamically
        self.desc_label = QLabel(f"<span id='cardDescText'>{description}</span>")
        self.desc_label.setWordWrap(True)
        self.desc_label.setObjectName("cardDescLabel")
        self.desc_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        text_layout.addWidget(self.desc_label)
        layout.addLayout(text_layout)
        
        
        self.setLayout(layout)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = ActionCard(
        title= 'title',
        icon_text= '',
        description= 'description'

    )
    window.show()
    sys.exit(app.exec())