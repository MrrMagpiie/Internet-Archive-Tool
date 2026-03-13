from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel, QLineEdit, 
    QFormLayout, QMessageBox,QHBoxLayout, QPushButton,
)
from PyQt6.QtCore import pyqtSignal, Qt, pyqtSlot
from model.service.signals import JobTicket

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from model.service.signals import JobTicket,DatabaseTicket

# ==========================================
# PAGE 1: Internet Archive Link
# ==========================================
from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFormLayout, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt
from model.service.signals import JobTicket

# ==========================================
# PAGE 1: Internet Archive Link
# ==========================================
class IAPage(QWizardPage):
    # Emit this to the Wizard, which will pass it to the DatabaseManager
    verify_ia_creds = pyqtSignal(tuple,JobTicket) 

    def __init__(self):
        super().__init__()
        self.setTitle("1. Link Internet Archive")
        self.setSubTitle("We need to securely retrieve your S3 API keys.")
        
        # This boolean acts as our lock for the "Next" button
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
        
        # --- NEW: The Action Button ---
        btn_layout = QHBoxLayout()
        self.btn_retrieve = QPushButton("Retrieve Keys")
        self.btn_retrieve.setObjectName("primaryActionBtn")
        self.btn_retrieve.clicked.connect(self.attempt_retrieval)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_retrieve)
        layout.addLayout(btn_layout)
        
        # Note: We DO NOT use registerField("ia_email*") here anymore, 
        # because we are manually controlling the "Next" button with isComplete()
        
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
        
        # Fire to the backend!
        self.verify_ia_creds.emit((access, secret),ticket)

    @pyqtSlot(object, str)
    def _handle_setup_success(self, success, job_id):
        if success:
            QMessageBox.information(self, "Success", "Internet Archive credentials configured successfully!")
            
            # 1. Update our lock boolean
            self.keys_retrieved = True 
            
            # 2. Tell the QWizard to re-check the `isComplete()` function!
            # This is the magic line that instantly turns the "Next" button blue.
            self.completeChanged.emit() 
            
            # 3. Polish: Lock the inputs and turn the button green so they know it's done
            self.btn_retrieve.setText("Keys Secured")
            self.btn_retrieve.setObjectName("successBtn") 
            self.btn_retrieve.setStyleSheet("") # Force QSS refresh
            self.ia_email_input.setEnabled(False)
            self.ia_pass_input.setEnabled(False)
        else:
            self._handle_setup_error("Unknown failure during configuration.", job_id)

    @pyqtSlot(str, str)
    def _handle_setup_error(self, error_msg, job_id):
        self.btn_retrieve.setEnabled(True)
        self.btn_retrieve.setText("Retrieve Keys")
        QMessageBox.critical(self, "Error", f"Internet Archive configuration failed: {error_msg}")

# ==========================================
# PAGE 2: Local Admin Setup
# ==========================================
class AdminPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("2. Create Local Administrator")
        self.setSubTitle("Set up the master account for this machine.")
        
        layout = QVBoxLayout()
        
        instructions = QLabel(
            "This account will have full access to modify schemas, delete records, "
            "and manage the local database."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        form = QFormLayout()
        
        self.admin_user_input = QLineEdit()
        self.admin_user_input.setObjectName("formLineEdit")
        
        self.admin_pass_input = QLineEdit()
        self.admin_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.admin_pass_input.setObjectName("formLineEdit")
        
        self.admin_confirm_input = QLineEdit()
        self.admin_confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.admin_confirm_input.setObjectName("formLineEdit")
        
        form.addRow("<b>Username:</b>", self.admin_user_input)
        form.addRow("<b>Password:</b>", self.admin_pass_input)
        form.addRow("<b>Confirm:</b>", self.admin_confirm_input)
        layout.addLayout(form)
        
        # Make these fields mandatory for the "Finish" button to unlock
        self.registerField("admin_user*", self.admin_user_input)
        self.registerField("admin_pass*", self.admin_pass_input)
        self.registerField("admin_confirm*", self.admin_confirm_input)
        
        self.setLayout(layout)

    def validatePage(self):
        """This runs when the user clicks 'Finish'. We use it to check for typos."""
        password = self.field("admin_pass")
        confirm = self.field("admin_confirm")
        
        if password != confirm:
            QMessageBox.warning(self, "Mismatch", "Admin passwords do not match!")
            return False # Stops the wizard from closing
            
        return True # Allows the wizard to finish


# ==========================================
# THE MAIN WIZARD CONTAINER
# ==========================================
class FirstRunSetupWizard(QWizard):
    # Signal 1: The IA key request
    ia_creds_request = pyqtSignal(tuple,JobTicket) 
    # Signal 2: The final payload with the local admin account details
    admin_setup_data = pyqtSignal(tuple,DatabaseTicket) 
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Archive Pipeline - Initial Setup")
        self.setFixedSize(500, 450)
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        
        # Instantiate pages
        self.ia_page = IAPage()
        self.admin_page = AdminPage() # (From the previous code block)
        
        # Link the IA Page signal up through the Wizard
        self.ia_page.verify_ia_creds.connect(self.ia_creds_request.emit)
        
        self.addPage(self.ia_page)
        self.addPage(self.admin_page)

    def accept(self):
        """Triggered when they hit 'Finish' on the final Admin Page."""
        payload = (self.admin_page.field("admin_user"),self.admin_page.field("admin_pass"))
        
        self.button(QWizard.WizardButton.FinishButton).setEnabled(False)
        self.button(QWizard.WizardButton.BackButton).setEnabled(False)
        self.button(QWizard.WizardButton.FinishButton).setText("Configuring...")

        ticket = DatabaseTicket()
        ticket.data.connect(self._handle_admin_success)
        ticket.error.connect(self._handle_admin_error)
        
        self.admin_setup_data.emit(payload,ticket)

    def _handle_admin_success(self, success, job_id):
        if success:
            QMessageBox.information(self, "Success", "Initial setup complete! You may now log in.")
            super().accept()

    def _handle_admin_error(self, error_msg, job_id):
        self.button(QWizard.WizardButton.FinishButton).setEnabled(True)
        self.button(QWizard.WizardButton.BackButton).setEnabled(True)
        self.button(QWizard.WizardButton.FinishButton).setText("Finish")
        QMessageBox.critical(self, "Setup Failed", f"Configuration failed: {error_msg}")