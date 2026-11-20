from cryptography.fernet import Fernet

from src.config import settings

cipher = Fernet(settings.ENCRYPTION_KEY.encode())


def encrypt_data(data: str) -> str:
    return cipher.encrypt(data.encode()).decode()


def decrypt_data(data: str) -> str:
    return cipher.decrypt(data.encode()).decode()
