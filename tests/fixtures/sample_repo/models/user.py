from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """User entity model representing an application user."""
    id: int
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
