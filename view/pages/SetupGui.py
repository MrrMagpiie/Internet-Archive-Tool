from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from model.service.signals import JobTicket

class FirstRunSetupDialog(QDialog):
    creds = pyqtSignal(object, object)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Archive Pipeline - Initial Setup")
        self.setFixedSize(500, 350)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        # 1. Welcome Header
        lbl_title = QLabel("Welcome to the Digitization Pipeline")
        lbl_title.setObjectName("pageTitle") # REUSED: Global Typography Hook
        layout.addWidget(lbl_title)
        
        # 2. Instructions with a clickable link
        instructions = QLabel(
            "Before you can begin scanning and processing documents, you must "
            "link this application to the Internet Archive.<br><br>"
            "Your email and password will not be saved.<br>" 
            "They are only used once to securely retrieve your S3 API keys, "
            "which can be managed at any time from IA's website:<br>" 
            "<a href='https://archive.org/account/s3.php'>archive.org/account/s3.php</a>"
        )
        instructions.setWordWrap(True)
        instructions.setOpenExternalLinks(True) 
        # FIXED: Removed inline color so qdarktheme automatically handles Light/Dark readability
        layout.addWidget(instructions)
        
        # 3. The Input Form
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.access_input = QLineEdit()
        self.access_input.setPlaceholderText("Enter your IA Email here...")
        self.access_input.setObjectName("formLineEdit") # REUSED: Global Input Hook
        
        self.secret_input = QLineEdit()
        self.secret_input.setPlaceholderText("Enter your IA Password here...")
        self.secret_input.setEchoMode(QLineEdit.EchoMode.Password) 
        self.secret_input.setObjectName("formLineEdit") # REUSED: Global Input Hook
        
        form_layout.addRow("<b>IA Email:</b>", self.access_input)
        form_layout.addRow("<b>IA Password:</b>", self.secret_input)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # 4. Action Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_quit = QPushButton("Exit")
        self.btn_quit.clicked.connect(self.reject) 
        
        self.btn_save = QPushButton("Retrieve Keys") # FIXED Typo
        self.btn_save.setObjectName("successBtn") # REUSED: Global Green Button
        self.btn_save.clicked.connect(self.save_credentials)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_quit)
        btn_layout.addWidget(self.btn_save)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save_credentials(self):
        """Validates inputs and creates the settings.json file."""
        access = self.access_input.text().strip()
        secret = self.secret_input.text().strip()
        
        if not access or not secret:
            QMessageBox.warning(self, "Missing Information", "Both keys are required to proceed.")
            return
            
        # UX Polish: Disable button while fetching to prevent network spam
        self.btn_save.setEnabled(False)
        self.btn_save.setText("Retrieving...")

        ticket = JobTicket()
        ticket.data.connect(self._handle_setup_success)
        ticket.error.connect(self._handle_setup_error)
        self.creds.emit(ticket, (access, secret))

    @pyqtSlot(object, str)
    def _handle_setup_success(self, success, job_id):
        """Callback for when the IA configuration is successful."""
        self.btn_save.setEnabled(True)
        self.btn_save.setText("Retrieve Keys")
        
        if success:
            QMessageBox.information(self, "Success", "Internet Archive credentials configured successfully.")
            self.accept()

    @pyqtSlot(str, str)
    def _handle_setup_error(self, error_msg, job_id):
        """Callback for when the IA configuration fails."""
        self.btn_save.setEnabled(True)
        self.btn_save.setText("Retrieve Keys")
        
        QMessageBox.critical(self, "Error", f"Internet Archive configuration failed: {error_msg}")