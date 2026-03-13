import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
    QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtSlot
from model.service.signals import JobTicket

# --- A Single Row in the Process List ---
class ProcessItem(QFrame):
    cancel_requested = pyqtSignal(str) # Signal to stop the thread

    def __init__(self, title, ticket: JobTicket):
        super().__init__()
        self.ticket = ticket
        self.setFixedHeight(50)
        
        # 1. NEW: Assign ID for the container
        self.setObjectName("processItem")
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Label
        self.lbl_name = QLabel(title)
        self.lbl_name.setObjectName("processItemLabel")

        self.step_lbl = QLabel()
        self.step_lbl.setObjectName("processItemStep")
        
        # Progress Bar
        self.pbar = QProgressBar()
        self.pbar.setFixedHeight(8)
        self.pbar.setTextVisible(False)
        self.pbar.setObjectName("processItemProgressBar")
        
        # Cancel Button
        btn_cancel = QPushButton("✕")
        btn_cancel.setFixedSize(24, 24)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setToolTip("Cancel Process")
        btn_cancel.setObjectName("processItemCancelBtn")
        btn_cancel.clicked.connect(self.cancel)
        
        # Layout Assembly
        v_col = QVBoxLayout()
        v_col.setSpacing(2)
        v_col.setContentsMargins(0, 0, 0, 0)
        v_col.addWidget(self.lbl_name)
        v_col.addWidget(self.step_lbl)
        v_col.addWidget(self.pbar)
        
        layout.addWidget(btn_cancel)
        layout.addLayout(v_col)
        self.setLayout(layout)

    def update_progress(self, value, step_text):
        self.pbar.setValue(value)
        if step_text:
            self.step_lbl.setText(step_text)
    
    def cancel(self):
        self.ticket.cancel()
        self.cancel_requested.emit(self.ticket.job_id)


# --- The Main Expandable Widget ---
class ProcessManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.active_tasks = {} 
        self.is_expanded = False
        
        # --- Constants for our Math ---
        self.ITEM_HEIGHT = 50
        self.MAX_LIST_HEIGHT = 400 # Caps out at 4 items before scrolling
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        # Data storage
        self.active_tasks = {} # {id: ProcessItem_widget}
        
        # Layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # --- 1. The Expandable List Area ---
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout()
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(0)
        self.list_layout.addStretch() 
        self.list_container.setLayout(self.list_layout)
        
        # Scroll Area wrapper
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.list_container)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setMaximumHeight(0)
        self.scroll_area.setObjectName("processScrollArea")
        
        # --- 2. The Header ---
        self.header = QFrame()
        self.header.setFixedHeight(40)
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.mousePressEvent = self.toggle_expand
        self.header.setObjectName("processHeader")
        
        # Header Layout
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        self.lbl_summary = QLabel("No active processes")
        self.lbl_summary.setObjectName("processSummaryLabel")
        self.lbl_icon = QLabel("▼")
        
        header_layout.addWidget(self.lbl_summary)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_icon)
        self.header.setLayout(header_layout)
        
        
        self.layout.addWidget(self.scroll_area)
        self.layout.addWidget(self.header)
        
        self.setLayout(self.layout)

    def toggle_expand(self,event):
        self.is_expanded = not self.is_expanded
        self._animate_height(self.get_target_height())

    # --- NEW: Dynamic Height Calculation ---
    def get_target_height(self):
        """Calculates exactly how tall the drawer should be."""
        if not self.is_expanded or len(self.active_tasks) == 0:
            return 0
        
        calculated_height = len(self.active_tasks) * self.ITEM_HEIGHT
        
        return min(calculated_height, self.MAX_LIST_HEIGHT)

    # --- NEW: Reusable Animation Logic ---
    def _animate_height(self, target_height):
        if hasattr(self, 'anim') and self.anim.state() == QPropertyAnimation.State.Running:
            self.anim.stop()
            
        self.anim = QPropertyAnimation(self.scroll_area, b"maximumHeight")
        self.anim.setDuration(250)
        self.anim.setStartValue(self.scroll_area.height())
        self.anim.setEndValue(target_height)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self.anim.valueChanged.connect(self.scroll_area.setMinimumHeight)
        
        # FIXED: Force the scrollbar to stay at the absolute bottom on every frame of the animation
        self.anim.valueChanged.connect(self._keep_scrolled_to_bottom)
        self.lbl_icon.setText("▲" if self.is_expanded else "▼")
        self.anim.start()

    # Add this tiny helper function anywhere in the class
    def _keep_scrolled_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @pyqtSlot(str, str, object)
    def add_task(self, task_command, task_item, ticket):
        if ticket.job_id in self.active_tasks:
            return
        ticket.canceled.connect(self.remove_task)
        task_name = f'{task_command} {task_item}'
        item = ProcessItem(task_name, ticket)
        item.cancel_requested.connect(self.remove_task)
        
        self.list_layout.addWidget(item)
        self.active_tasks[ticket.job_id] = item
        
        self.update_summary()
        
        # NEW: Automatically grow the drawer if it's already open!
        if self.is_expanded:
            self._animate_height(self.get_target_height())

    @pyqtSlot(str)
    def remove_task(self, job_id):
        if job_id in self.active_tasks:
            widget = self.active_tasks.pop(job_id)
            widget.deleteLater()
            self.update_summary()
            
            # Automatically shrink the drawer to fit the remaining items
        if self.is_expanded:
            self._animate_height(self.get_target_height())
            
    @pyqtSlot(str, int, object)
    def update_task_progress(self, job_id, progress, step_text):
        if job_id in self.active_tasks:
            self.active_tasks[job_id].update_progress(progress, step_text)

    @pyqtSlot()
    def update_summary(self):
        count = len(self.active_tasks)
        if count == 0:
            self.lbl_summary.setText("No active processes")
        else:
            self.lbl_summary.setText(f"{count} Processes Running...")