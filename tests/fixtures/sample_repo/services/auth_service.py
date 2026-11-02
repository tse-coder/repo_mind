from typing import Optional
from tests.fixtures.sample_repo.models.user import User
from tests.fixtures.sample_repo.utils.helpers import hash_password, generate_token


class AuthService:
    """Service handling user authentication and token creation."""

    def __init__(self):
        self._users: dict[str, User] = {}

    def register_user(self, username: str, email: str, password: str) -> User:
        """Register a new user account."""
        if username in self._users:
            raise ValueError(f"User {username} already exists")
        hashed = hash_password(password)
        user = User(
            id=len(self._users) + 1,
            username=username,
            email=email,
            hashed_password=hashed,
        )
        self._users[username] = user
        return user

    def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate user credentials and return session token."""
        user = self._users.get(username)
        if not user or user.hashed_password != hash_password(password):
            return None
        return generate_token()
