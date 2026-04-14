# Файл: core/encryption.py
"""
Модуль шифрования AES-256 для Cronos
Использует PBKDF2 для деривации ключа и Fernet для шифрования
"""

import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet


def derive_key(password: str, salt: bytes) -> bytes:
    """Деривация ключа из пароля с помощью PBKDF2"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def get_fernet(password: str, salt: bytes = None) -> tuple:
    """Создать Fernet экземпляр для шифрования/дешифрования"""
    if salt is None:
        salt = os.urandom(16)
    
    key = derive_key(password, salt)
    fernet = Fernet(key)
    
    return fernet, salt


def encrypt_data(data: bytes, password: str, salt: bytes = None) -> tuple:
    """Зашифровать данные"""
    fernet, salt = get_fernet(password, salt)
    encrypted = fernet.encrypt(data)
    return encrypted, salt


def decrypt_data(encrypted_data: bytes, password: str, salt: bytes) -> bytes:
    """Расшифровать данные"""
    key = derive_key(password, salt)
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_data)
