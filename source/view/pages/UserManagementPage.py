from PyQt6.QtWidgets import (
    QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, 
    QCheckBox, QMessageBox, QListWidget, QListWidgetItem, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal
from view.components import Page
from model.service.Signals import DatabaseTicket


class UsersPage(Page):
    request_users = pyqtSignal(DatabaseTicket)
    request_new_user = pyqtSignal(tuple,DatabaseTicket)
    request_user_delete = pyqtSignal(str,DatabaseTicket)
    def __init__(self, parent=None):
        super().__init__(parent)
        self._create_layout()

    
    def _create_layout(self):
        layout = QVBoxLayout(self)
        
        lbl_users = QLabel("Manage Users")
        lbl_users.setObjectName("sectionTitle")
        layout.addWidget(lbl_users)
        
        self.user_list = QListWidget()
        layout.addWidget(self.user_list)
        
        btn_layout = QHBoxLayout()
        self.btn_refresh_users = QPushButton("Refresh Users")
        self.btn_refresh_users.clicked.connect(self.load_users)
        self.btn_remove_user = QPushButton("Remove Selected User")
        self.btn_remove_user.setObjectName("dangerBtn")
        self.btn_remove_user.clicked.connect(self.remove_user)
        
        btn_layout.addWidget(self.btn_refresh_users)
        btn_layout.addWidget(self.btn_remove_user)
        layout.addLayout(btn_layout)
        
        layout.addSpacing(20)
        lbl_add = QLabel("Add New User")
        lbl_add.setObjectName("sectionTitle")
        layout.addWidget(lbl_add)
        
        form = QFormLayout()
        self.new_username = QLineEdit()
        self.new_password = QLineEdit()
        self.admin_role = QCheckBox("Admin")
        self.admin_role.setChecked(False)
        
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Username:", self.new_username)
        form.addRow("Password:", self.new_password)
        form.addRow('Admin:',self.admin_role)
        layout.addLayout(form)
        
        self.btn_add_user = QPushButton("Add User")
        self.btn_add_user.setObjectName("primaryActionBtn")
        self.btn_add_user.clicked.connect(self.add_user)
        layout.addWidget(self.btn_add_user)

    def load_users(self):
        ticket = DatabaseTicket()
        ticket.data.connect(self._on_users_loaded)
        self.request_users.emit(ticket)

    @pyqtSlot(object, str)
    def _on_users_loaded(self, users, job_id):
        self.user_list.clear()
        for u in users:
            item = QListWidgetItem(f"{u['username']} ({u['role']})")
            item.setData(Qt.ItemDataRole.UserRole, u['user_id'])
            self.user_list.addItem(item)

    def remove_user(self):
        selected = self.user_list.currentItem()
        if not selected:
            return
        user_id = str(selected.data(Qt.ItemDataRole.UserRole))
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to remove user: {selected.text()}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            ticket = DatabaseTicket()
            ticket.data.connect(self._on_user_removed)
            ticket.error.connect(self._on_user_error)
            self.request_user_delete.emit(user_id,ticket)

    @pyqtSlot(object, str)
    def _on_user_removed(self, success, job_id):
        if success:
            QMessageBox.information(self, "Success", "User removed successfully.")
            self.load_users()

    def add_user(self):
        username = self.new_username.text().strip()
        password = self.new_password.text()
        is_admin = self.admin_role.isChecked()
        if is_admin: role = 'admin' 
        else: role = 'user'
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and password required.")
            return
            
        ticket = DatabaseTicket()
        ticket.data.connect(self._on_user_added)
        ticket.error.connect(self._on_user_error)
        
        self.request_new_user.emit((username, password, role), ticket)

    @pyqtSlot(object, str)
    def _on_user_added(self, success, job_id):
        if success:
            QMessageBox.information(self, "Success", "User added successfully.")
            self.new_username.clear()
            self.new_password.clear()
            self.load_users()

    @pyqtSlot(Exception, str)
    def _on_user_error(self, error, job_id):
        QMessageBox.critical(self, "Error", str(error))