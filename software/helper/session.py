from cryptography.fernet import Fernet
from flask import current_app as app

REQUIRED_SESSION_VALUES = ['uuid', 'config', 'key']


def human_code() -> bytes:
    return Fernet.generate_key()


def valid_user_session(session: dict) -> bool:
    for value in REQUIRED_SESSION_VALUES:
        if value not in session:
            return False

    return True
