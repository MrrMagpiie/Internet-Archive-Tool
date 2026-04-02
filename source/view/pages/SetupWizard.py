from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel, QLineEdit, 
    QFormLayout, QMessageBox,QHBoxLayout, QPushButton
)
from PyQt6.QtCore import pyqtSignal, Qt, pyqtSlot
from model.service.Signals import JobTicket, DatabaseTicket


# ==========================================
# PAGE 1: Internet Archive Link
# ==========================================
class IAPage(QWizardPage):
    verify_ia_creds = pyqtSignal(tuple,JobTicket)

    def __init__(self):
        super().__init__()
        self.setTitle("Link Internet Archive")
        self.setSubTitle("We need to securely retrieve your S3 API keys.")

        self.keys_retrieved = False 
        
        layout = QVBoxLayout()
        
        instructions = QLabel(
            "Your email and password are used once to retrieve your keys. "
            "Manage them anytime at <a href='https://archive.org/account/s3.php'>archive.org/account/s3.php</a>"
        )
        instructions.setWordWrap(True)
        instructions.setOpenExternalLinks(True) 
        layout.addWidget(instructions)
        
        form = QFormLayout()
        
        self.ia_email_input = QLineEdit()
        self.ia_email_input.setPlaceholderText("IA Email...")
        self.ia_email_input.setObjectName("formLineEdit")
        
        self.ia_pass_input = QLineEdit()
        self.ia_pass_input.setPlaceholderText("IA Password...")
        self.ia_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.ia_pass_input.setObjectName("formLineEdit")
        
        form.addRow("<b>IA Email:</b>", self.ia_email_input)
        form.addRow("<b>IA Password:</b>", self.ia_pass_input)
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        self.btn_retrieve = QPushButton("Retrieve Keys")
        self.btn_retrieve.setObjectName("primaryActionBtn")
        self.btn_retrieve.clicked.connect(self.attempt_retrieval)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_retrieve)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)

    def isComplete(self):
        """
        QWizard automatically checks this function to see if the 'Next' 
        button should be enabled. If it returns False, the user is stuck here.
        """
        return self.keys_retrieved

    def attempt_retrieval(self):
        access = self.ia_email_input.text().strip()
        secret = self.ia_pass_input.text().strip()
        
        if not access or not secret:
            QMessageBox.warning(self, "Missing Information", "Both keys are required to proceed.")
            return
            
        # Lock the button to prevent spamming
        self.btn_retrieve.setEnabled(False)
        self.btn_retrieve.setText("Retrieving...")

        ticket = JobTicket()
        ticket.data.connect(self._handle_setup_success)
        ticket.error.connect(self._handle_setup_error)
        
        self.verify_ia_creds.emit((access, secret),ticket)

    @pyqtSlot(object, str)
    def _handle_setup_success(self, success, job_id):
        if success:
            QMessageBox.information(self, "Success", "Internet Archive credentials configured successfully!")
            
            self.keys_retrieved = True 
    
            self.completeChanged.emit() 
            
            self.btn_retrieve.setText("Keys Secured")
            self.btn_retrieve.setObjectName("successBtn") 
            self.btn_retrieve.setStyleSheet("") # Force QSS refresh
            self.ia_email_input.setEnabled(False)
            self.ia_pass_input.setEnabled(False)
        else:
            self._handle_setup_error("Unknown failure during configuration.", job_id)

    @pyqtSlot(Exception, str)
    def _handle_setup_error(self, error, job_id):
        self.btn_retrieve.setEnabled(True)
        self.btn_retrieve.setText("Retrieve Keys")
        QMessageBox.critical(self, "Error", f"Internet Archive configuration failed: {error}")

# ==========================================
# PAGE 2: Local Admin Setup
# ==========================================
class AdminPage(QWizardPage):
    admin_setup_data = pyqtSignal(tuple, DatabaseTicket) 
    
    def __init__(self):
        super().__init__()
        self.setTitle("Create Local Administrator")
        self.setSubTitle("Set up the master account for this machine.")
        
        self.admin_created = False
        
        layout = QVBoxLayout()
        form = QFormLayout()
        
        self.admin_user_input = QLineEdit()
        self.admin_pass_input = QLineEdit()
        self.admin_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.admin_confirm_input = QLineEdit()
        self.admin_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        form.addRow("<b>Username:</b>", self.admin_user_input)
        form.addRow("<b>Password:</b>", self.admin_pass_input)
        form.addRow("<b>Confirm:</b>", self.admin_confirm_input)
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("Create Account")
        self.btn_save.clicked.connect(self.attempt_creation)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)

    def isComplete(self):
        """Keeps the Wizard's 'Next' or 'Finish' button disabled until success."""
        return self.admin_created

    def attempt_creation(self):
        # 1. Local Validation
        user = self.admin_user_input.text().strip()
        password = self.admin_pass_input.text()
        confirm = self.admin_confirm_input.text()
        
        if not user or not password:
            QMessageBox.warning(self, "Missing Info", "Username and password required.")
            return
            
        if password != confirm:
            QMessageBox.warning(self, "Mismatch", "Passwords do not match!")
            return

        # 2. Lock the UI and fire the worker
        self.btn_save.setEnabled(False)
        self.btn_save.setText("Creating...")

        ticket = DatabaseTicket()
        ticket.data.connect(self._handle_admin_success)
        ticket.error.connect(self._handle_admin_error)
        
        self.admin_setup_data.emit((user, password), ticket)

    @pyqtSlot(object, str)
    def _handle_admin_success(self, success, job_id):
        if success:
            QMessageBox.information(self, "Success", "Administrator created!")
            self.admin_created = True 
            
            # Unlock the Wizard's Next/Finish button!
            self.completeChanged.emit() 
            
            self.btn_save.setText("Account Created")
            self.admin_user_input.setEnabled(False)
            self.admin_pass_input.setEnabled(False)
            self.admin_confirm_input.setEnabled(False)

    @pyqtSlot(Exception, str)
    def _handle_admin_error(self, error, job_id):
        self.btn_save.setEnabled(True)
        self.btn_save.setText("Create Account")
        QMessageBox.critical(self, "Error", f"Failed to create admin: {error}")


# ==========================================
# THE MAIN WIZARD CONTAINER
# ==========================================
class SetupWizard(QWizard):    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Archive Pipeline - Initial Setup")
        self.setFixedSize(500, 450)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
