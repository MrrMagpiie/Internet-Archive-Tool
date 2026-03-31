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

class ProcessCategoryWidget(QFrame):
    height_changed = pyqtSignal()
    empty = pyqtSignal(str)       
    def __init__(self, category_name):
        super().__init__()
        self.category_name = category_name
        self.items = {}
        self.is_expanded = False
        
        self.HEADER_HEIGHT = 40
        self.ITEM_HEIGHT = 60
        
        self.setObjectName("processCategoryWidget")
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # --- Category Header ---
        self.header = QFrame()
        self.header.setFixedHeight(self.HEADER_HEIGHT)
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.mousePressEvent = self.toggle_expand
        self.header.setStyleSheet("background-color: rgba(0,0,0,0.05); border-bottom: 1px solid rgba(0,0,0,0.1);")
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 0, 15, 0)
        
        self.lbl_title = QLabel(f"{category_name.capitalize()} (0)")
        self.lbl_title.setStyleSheet("font-weight: bold;")
        self.lbl_icon = QLabel("▼")
        
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_icon)
        self.header.setLayout(header_layout)
        
        # --- Items Container ---
        self.item_container = QWidget()
        self.item_layout = QVBoxLayout()
        self.item_layout.setContentsMargins(10, 0, 0, 0) 
        self.item_layout.setSpacing(0)
        self.item_container.setLayout(self.item_layout)
        self.item_container.setVisible(False) 
        
        self.layout.addWidget(self.header)
        self.layout.addWidget(self.item_container)
        self.setLayout(self.layout)

    def toggle_expand(self, event=None):
        if len(self.items) == 0: return
        self.is_expanded = not self.is_expanded
        self.item_container.setVisible(self.is_expanded)
        self.lbl_icon.setText("▲" if self.is_expanded else "▼")
        self.height_changed.emit()

    def add_task(self, item_widget, job_id):
        self.items[job_id] = item_widget
        self.item_layout.addWidget(item_widget)
        self.update_title()
        self.height_changed.emit()

    def remove_task(self, job_id):
        if job_id in self.items:
            item = self.items.pop(job_id)
            item.deleteLater()
            self.update_title()
            
            if len(self.items) == 0:
                self.empty.emit(self.category_name)
            else:
                self.height_changed.emit()

    def update_task(self, job_id, progress, step_text):
        if job_id in self.items:
            self.items[job_id].update_progress(progress, step_text)

    def update_title(self):
        self.lbl_title.setText(f"{self.category_name.capitalize()} ({len(self.items)})")

    def get_target_height(self):
        """Calculates how tall this specific category block is."""
        h = self.HEADER_HEIGHT
        if self.is_expanded:
            h += len(self.items) * self.ITEM_HEIGHT
        return h

# --- The Main Expandable Widget ---
class ProcessManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.is_expanded = False
        
        # --- Data Storage ---
        self.categories = {}
        self.task_routing = {}
        
        self.MAX_LIST_HEIGHT = 500
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        # --- 1. The Expandable List Area ---
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout()
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(0)
        self.list_layout.addStretch() 
        self.list_container.setLayout(self.list_layout)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.list_container)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setMaximumHeight(0)
        self.scroll_area.setObjectName("processScrollArea")
        
        # --- 2. The Master Header ---
        self.header = QFrame()
        self.header.setFixedHeight(50)
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.mousePressEvent = self.toggle_expand
        self.header.setObjectName("processHeader")
        
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

    def toggle_expand(self, event=None):
        self.is_expanded = not self.is_expanded
        self._recalculate_height()

    def _recalculate_height(self):
        """Triggers the animation to perfectly fit all expanded categories."""
        if not self.is_expanded or len(self.task_routing) == 0:
            target = 0
        else:
            total_h = sum(cat.get_target_height() for cat in self.categories.values())
            target = min(total_h, self.MAX_LIST_HEIGHT)
            
        self._animate_height(target)

    def _animate_height(self, target_height):
        if hasattr(self, 'anim') and self.anim.state() == QPropertyAnimation.State.Running:
            self.anim.stop()
            
        self.anim = QPropertyAnimation(self.scroll_area, b"maximumHeight")
        self.anim.setDuration(250)
        self.anim.setStartValue(self.scroll_area.height())
        self.anim.setEndValue(target_height)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        
        self.anim.valueChanged.connect(self.scroll_area.setMinimumHeight)
        self.anim.valueChanged.connect(self._keep_scrolled_to_bottom)
        self.lbl_icon.setText("▲" if self.is_expanded else "▼")
        self.anim.start()

    def _keep_scrolled_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @pyqtSlot(str, str, object)
    def add_task(self, task_command, task_item, ticket):
        if ticket.job_id in self.task_routing:
            return
            
        # 1. Ensure the category widget exists
        if task_command not in self.categories:
            cat_widget = ProcessCategoryWidget(task_command)
            cat_widget.height_changed.connect(self._recalculate_height)
            cat_widget.empty.connect(self._remove_category)
            
            self.categories[task_command] = cat_widget
            self.list_layout.insertWidget(self.list_layout.count() - 1, cat_widget)

        # 2. Build and route the item
        ticket.canceled.connect(self.remove_task)
        item = ProcessItem(f"{task_command} {task_item}", ticket)
        item.cancel_requested.connect(self.remove_task)
        
        self.task_routing[ticket.job_id] = task_command
        self.categories[task_command].add_task(item, ticket.job_id)
        
        self.update_summary()

    @pyqtSlot(str)
    def remove_task(self, job_id):
        if job_id in self.task_routing:
            category_name = self.task_routing.pop(job_id)
            self.categories[category_name].remove_task(job_id)
            self.update_summary()

    @pyqtSlot(str)
    def _remove_category(self, category_name):
        """Called automatically when a category runs out of items."""
        if category_name in self.categories:
            widget = self.categories.pop(category_name)
            widget.deleteLater()
            self._recalculate_height()

    @pyqtSlot(str, int, str)
    def update_task_progress(self, job_id, progress, step_text):
        if job_id in self.task_routing:
            category_name = self.task_routing[job_id]
            self.categories[category_name].update_task(job_id, progress, step_text)

    @pyqtSlot()
    def update_summary(self):
        count = len(self.task_routing)
        if count == 0:
            self.lbl_summary.setText("No active processes")
            self.is_expanded = False
            self._recalculate_height()
        else:
            self.lbl_summary.setText(f"{count} Processes Running...")