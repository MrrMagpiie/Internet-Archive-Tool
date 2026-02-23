import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QListWidget, QStackedWidget, QLabel, QPushButton, QSplitter, 
    QListWidgetItem, QFrame, QFormLayout, QLineEdit, QDateEdit,
    QProgressBar, QComboBox, QGraphicsView, QGraphicsScene,QGridLayout,
    QScrollArea,QSizePolicy, QLayout,QStyle
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QIcon, QFont, QColor, QCursor,QPixmap,QPainter,QAction

class CenteredFlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        # Add margins
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()
        
        # This list will hold items for the current row
        current_row_items = []
        
        # Helper to process a finished row
        def layout_row(items, row_y, row_height):
            if not items:
                return

            # 1. Calculate total width of this row's content
            total_content_width = 0
            for item in items:
                total_content_width += item.sizeHint().width()
            
            # Add spacing between items
            if len(items) > 1:
                total_content_width += spacing * (len(items) - 1)

            # 2. Calculate the offset to center everything
            available_width = rect.width()
            offset_x = rect.x() + (available_width - total_content_width) / 2
            
            # 3. Place the items
            current_x = offset_x
            for item in items:
                if not test_only:
                    item.setGeometry(QRect(QPoint(int(current_x), int(row_y)), item.sizeHint()))
                
                current_x += item.sizeHint().width() + spacing

        # --- Main Layout Loop ---
        for item in self.itemList:
            wid = item.widget()
            space_x = spacing 
            
            next_x = x + item.sizeHint().width() + space_x
            
            # If adding this item exceeds the width, finish the current row
            if next_x - space_x > rect.right() and line_height > 0:
                layout_row(current_row_items, y, line_height)
                
                # Reset for next row
                current_row_items = []
                x = rect.x()
                y = y + line_height + spacing
                line_height = 0

            # Add item to current row buffer
            current_row_items.append(item)
            x += item.sizeHint().width() + space_x
            line_height = max(line_height, item.sizeHint().height())

        # Layout the very last row
        layout_row(current_row_items, y, line_height)
        
        return y + line_height - rect.y()
