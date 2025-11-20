import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout,QGridLayout,
    QPushButton, QLabel, QStackedWidget,QApplication
)

from view.components.ActionCard import ActionCard



class ActionDashboard(QWidget):
    """The central starting point for the Task Dashboard layout, now with dynamic column switching."""
    threshold_height = 200

    def __init__(self,stack = None,parent =None):
        super().__init__(parent)
        self.cards = []
        self.stack = stack
        self.is_single_column = True
        if self.stack != None: 
            self.create_layout()
        
    def set_stack(self,stack):
        self.parent_stack = stack

    def create_layout(self):
        main_layout = QVBoxLayout(self)
        # --- Action Cards Grid Setup ---
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(15)
        self.is_single_column = True
        
        # Place the grid layout into the main layout
        main_layout.addLayout(self.cards_layout)
        
    def _clear_layout(self, layout):
        """Helper to remove all widgets from a layout."""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget() is not None:
                    item.widget().setParent(None)

    def new_card(self, title, icon_text, description,index=None):
        card = ActionCard(
            title, icon_text, description
        )
        if index != None:
            card.mousePressEvent = lambda e: self.stack.setCurrentIndex(index)
        self.cards.append(card)
        self.threshold_height += 100

    def _rearrange_cards(self, columns):
        """Restructures the QGridLayout based on the number of columns."""
        
        # Clear the current layout first
        self._clear_layout(self.cards_layout)
        
        row = 1
        column = 0
        if columns == 1:
            # 1-COLUMN LAYOUT: All cards stack vertically, 3 rows
            for card in self.cards:
                self.cards_layout.addWidget(card, row, 0)
                self.cards_layout.setRowStretch(row, 1) # Expandable
                row += 1
            
            # Ensure the right column (col 1) doesn't take space unnecessarily
            self.cards_layout.setColumnStretch(1, 0)

        elif columns == 2:
            # 2-COLUMN LAYOUT: Cards 1 and 2 side-by-side, Card 3 spans the row
            for card in self.cards:
                self.cards_layout.addWidget(card, row, column)
                column +=1
                if column == columns:
                    column = 0
                    row += 1


    def resizeEvent(self, event):
        """Overrides resize event to dynamically change card layout."""
        current_height = self.height()
        
        # Check if we need to switch from 1-column to 2-column (height shrinking)
        if self.is_single_column and current_height < self.threshold_height:
            self._rearrange_cards(2)
            self.is_single_column = False
        
        # Check if we need to switch from 2-column back to 1-column (height growing)
        elif not self.is_single_column and current_height >= self.threshold_height:
            self._rearrange_cards(1)
            self.is_single_column = True
        
        super().resizeEvent(event) # Call the parent's implementation

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    stack = QStackedWidget()
    green = QWidget()
    green.setStyleSheet('background-color:green;')
    stack.addWidget(green)
    window = ActionDashboard(stack)
    window.new_card(
        title= 'green',
        icon_text = '',
        description = 'desription',
        index = 0
    )
    window.show()
    sys.exit(app.exec())
    pass
