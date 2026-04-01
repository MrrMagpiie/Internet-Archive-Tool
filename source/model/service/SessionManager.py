class SessionManager:
    """A global state manager to track the currently logged-in user."""
    
    _current_user = None

    @classmethod
    def login(cls, username, role):
        cls._current_user = {
            "username": username,
            "role": role
        }
        print(f"Logged in as {username} ({role})")

    @classmethod
    def logout(cls):
        cls._current_user = None

    @classmethod
    def is_admin(cls):
        if not cls._current_user:
            return False
        return cls._current_user.get("role") == "admin"
        
    @classmethod
    def get_username(cls):
        if not cls._current_user:
            return "Guest"
        return cls._current_user.get("username")