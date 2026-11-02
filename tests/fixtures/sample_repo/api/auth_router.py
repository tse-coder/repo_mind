from tests.fixtures.sample_repo.services.auth_service import AuthService

auth_service = AuthService()


def login_handler(request: dict) -> dict:
    """HTTP POST handler for /api/login."""
    username = request.get("username", "")
    password = request.get("password", "")
    token = auth_service.authenticate(username, password)
    if not token:
        return {"error": "Invalid credentials", "status": 401}
    return {"token": token, "status": 200}


def register_handler(request: dict) -> dict:
    """HTTP POST handler for /api/register."""
    username = request.get("username", "")
    email = request.get("email", "")
    password = request.get("password", "")
    try:
        user = auth_service.register_user(username, email, password)
        return {"user_id": user.id, "username": user.username, "status": 201}
    except ValueError as e:
        return {"error": str(e), "status": 400}
