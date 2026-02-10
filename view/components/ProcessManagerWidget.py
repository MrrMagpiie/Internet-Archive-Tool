from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
    QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtSlot

# --- A Single Row in the Process List ---
class ProcessItem(QFrame):
    cancel_requested = pyqtSignal() # Signal to stop the thread

    def __init__(self, title, process_id):
        super().__init__()
        self.process_id = process_id
        self.setFixedHeight(50)
        self.setStyleSheet("""
            ProcessItem {
                background-color: white;
                border-bottom: 1px solid #e1e4e8;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        
        # 1. Label
        self.lbl_name = QLabel(title)
        self.lbl_name.setStyleSheet("font-weight: bold; color: #444;")
        
        # 2. Progress Bar
        self.pbar = QProgressBar()
        self.pbar.setFixedHeight(8)
        self.pbar.setTextVisible(False)
        self.pbar.setStyleSheet("""
            QProgressBar { background: #eee; border-radius: 4px; }
            QProgressBar::chunk { background: #2da44e; border-radius: 4px; }
        """)
        
        # 3. Cancel Button
        btn_cancel = QPushButton("✕")
        btn_cancel.setFixedSize(24, 24)
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setToolTip("Cancel Process")
        btn_cancel.setStyleSheet("""
            QPushButton {
                border: none; color: #999; font-weight: bold;
            }
            QPushButton:hover { color: #d73a49; background: #ffeef0; border-radius: 12px; }
        """)
        btn_cancel.clicked.connect(self.cancel_requested.emit)
        
        # Layout Assembly
        # Stack Label and Bar vertically for compactness
        v_col = QVBoxLayout()
        v_col.setSpacing(2)
        v_col.setContentsMargins(0,0,0,0)
        v_col.addWidget(self.lbl_name)
        v_col.addWidget(self.pbar)
        
        layout.addLayout(v_col)
        layout.addWidget(btn_cancel)
        self.setLayout(layout)

    def update_progress(self, value):
        self.pbar.setValue(value)

class Task():
    def __init__(command, doc_id, task_id):
        self.task_id = task_id
        self.command = command
        self.doc_id = doc_id


# --- The Main Expandable Widget ---
class ProcessManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # Data storage
        self.active_tasks = {} # {id: ProcessItem_widget}
        self.is_expanded = False
        
        # Layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # --- 1. The Expandable List Area (Hidden by default) ---
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout()
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(0)
        self.list_layout.addStretch() # Push items to bottom (so they stack up from header)
        self.list_container.setLayout(self.list_layout)
        
        # Scroll Area wrapper
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.list_container)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("border: none; background: #f6f8fa;")
        self.scroll_area.setFixedHeight(0) # Start hidden
        
        # --- 2. The Header (Always Visible) ---
        self.header = QFrame()
        self.header.setFixedHeight(40)
        self.header.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header.setStyleSheet("""
            QFrame {
                background-color: #24292e; 
                color: white;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QFrame:hover { background-color: #444d56; }
        """)
        
        # Header Layout
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(15, 0, 15, 0)
        
        self.lbl_summary = QLabel("No active processes")
        self.lbl_summary.setStyleSheet("font-weight: 600; font-size: 12px;")
        
        self.lbl_icon = QLabel("▲") # Up arrow implies "Click to expand up"
        
        header_layout.addWidget(self.lbl_summary)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_icon)
        self.header.setLayout(header_layout)
        
        # Click event to toggle
        self.header.mousePressEvent = self.toggle_expand
        
        # Add to main layout (Scroll Area ABOVE Header implies "Expand Up")
        self.layout.addWidget(self.scroll_area)
        self.layout.addWidget(self.header)
        
        self.setLayout(self.layout)
        
        # Hide entirely if no tasks
        self.setVisible(False)

    def toggle_expand(self, event):
        self.is_expanded = not self.is_expanded
        
        # Animate height
        target_height = 200 if self.is_expanded else 0
        
        self.anim = QPropertyAnimation(self.scroll_area, b"maximumHeight")
        self.anim.setDuration(300)
        self.anim.setStartValue(self.scroll_area.height())
        self.anim.setEndValue(target_height)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim.start()
        
        # Update Icon
        self.lbl_icon.setText("▼" if self.is_expanded else "▲")

        # Ensure layout updates
        self.anim.finished.connect(lambda: self.scroll_area.setFixedHeight(target_height))

    @pyqtSlot(str,str)
    def add_task(self, task_id, task_name):
        """Adds a new row to the list"""
        if task_id in self.active_tasks:
            return
            
        # Create item
        item = ProcessItem(task_name, task_id)
        
        # Connect cancel signal
        item.cancel_requested.connect(lambda: self.remove_task(task_id))
        
        # Add to layout (Insert at 0 to put new tasks at the bottom closest to header)
        self.list_layout.insertWidget(self.list_layout.count() - 1, item)
        self.active_tasks[task_id] = item
        
        self.update_summary()
        self.setVisible(True) # Show the bar

    @pyqtSlot(str, int)
    def update_task_progress(self, task_id, progress):
        if task_id in self.active_tasks:
            self.active_tasks[task_id].update_progress(progress)

    @pyqtSlot(str)
    def remove_task(self, task_id):
        if task_id in self.active_tasks:
            widget = self.active_tasks.pop(task_id)
            widget.deleteLater()
            self.update_summary()
            
            # Hide entire bar if empty
            if not self.active_tasks:
                self.setVisible(False)

    @pyqtSlot()
    def update_summary(self):
        count = len(self.active_tasks)
        if count == 0:
            self.lbl_summary.setText("No active processes")
        else:
            self.lbl_summary.setText(f"{count} Processes Running...")