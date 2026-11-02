"""
Application configuration with leaked credentials for secret scanner evaluation.
"""

APP_ENV = "production"
PORT = 8080

# Leaked credentials to verify secret redaction
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

def get_db_url() -> str:
    return "postgresql://admin:secret123@localhost:5432/appdb"

