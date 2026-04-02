from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from view.components.Page import Page
from model.service.SessionManager import SessionManager
from model.service.Signals import DatabaseTicket

class LoginPage(Page):
    login_successful = pyqtSignal()
    login_request = pyqtSignal(tuple,DatabaseTicket)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_layout()

    def _create_layout(self):
        main_layout = QVBoxLayout(self)
        
        # The Center Card
        center_box = QFrame()
        center_box.setObjectName("documentCard") 
        center_box.setFixedSize(350, 320)
        
        box_layout = QVBoxLayout(center_box)
        box_layout.setSpacing(15)

        # Title
        title = QLabel("Archive Login")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box_layout.addWidget(title)

        # Username Field
        self.username_input = QLineEdit()
        self.username_input.setObjectName("formLineEdit")
        self.username_input.setPlaceholderText("Username")
        # Pre-fill it for faster testing!
        self.username_input.setText("") 
        box_layout.addWidget(self.username_input)

        # Password Fiel
        self.password_input = QLineEdit()
        self.password_input.setObjectName("formLineEdit")
        self.password_input.setPlaceholderText("Password")
        # THIS is what masks the text as dots
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password) 
        # Allow hitting "Enter" to submit
        self.password_input.returnPressed.connect(self.attempt_login)
        box_layout.addWidget(self.password_input)

        # Login Button
        btn_login = QPushButton("Login")
        btn_login.setObjectName("primaryActionBtn")
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_login.clicked.connect(self.attempt_login)
        box_layout.addWidget(btn_login)

        # Divider Line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("schemaSectionLine")
        box_layout.addWidget(line)

        # Guest Button
        btn_guest = QPushButton("Continue as Guest")
        btn_guest.setObjectName("infoBtn")
        btn_guest.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guest.clicked.connect(self.login_as_guest)
        box_layout.addWidget(btn_guest)

        # Layout Assembly
        main_layout.addStretch()
        main_layout.addWidget(center_box, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch()

    def attempt_login(self):
        """Fires the credentials to the database worker."""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both username and password.")
            return

        # Create a ticket and listen for the database's answer
        ticket = DatabaseTicket()
        ticket.data.connect(self.handle_login_response)
        
        # Send the verification command
        self.login_request.emit((username, password),ticket)

    @pyqtSlot(dict, str)
    def handle_login_response(self, result: dict, job_id: str):
        """Processes the answer from the database worker."""
        if result['success']:
            SessionManager.login(result['username'], result['role'])
            self.password_input.clear() # Clear it for security
            self.login_successful.emit()
            self.close()
        else:
            QMessageBox.critical(self, "Access Denied", "Invalid username or password.")
            self.password_input.clear()
            self.password_input.setFocus() # Put the cursor back in the password box

    def login_as_guest(self):
        """Bypasses the database entirely for standard users."""
        SessionManager.login("Guest", "user")
        self.password_input.clear()
        self.login_successful.emit()