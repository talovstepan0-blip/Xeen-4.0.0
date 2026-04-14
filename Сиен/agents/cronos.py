# Файл: agents/cronos.py
"""
Агент Cronos - Хранилище секретов (AES-256)
Порт: 8004
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import logging
from datetime import datetime
from typing import Optional, Dict
import json
import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cronos")

app = FastAPI(title="Cronos Agent", version="1.0.0")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
SECRETS_FILE = os.path.join(DATA_DIR, "secrets.json.aes")

MASTER_PASSWORD = None
FERNET_INSTANCE = None


class SecretRequest(BaseModel):
    key: str
    value: str


class SecretGetRequest(BaseModel):
    key: str


class MasterPasswordRequest(BaseModel):
    password: str


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def init_encryption(password: str):
    global MASTER_PASSWORD, FERNET_INSTANCE
    
    if os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE, "rb") as f:
            salt = f.read(16)
    else:
        salt = os.urandom(16)
    
    key = derive_key(password, salt)
    FERNET_INSTANCE = Fernet(key)
    MASTER_PASSWORD = password
    
    if not os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE, "wb") as f:
            f.write(salt)
            f.write(FERNET_INSTANCE.encrypt(b"{}"))


def load_secrets() -> Dict[str, str]:
    if not FERNET_INSTANCE or not os.path.exists(SECRETS_FILE):
        return {}
    
    with open(SECRETS_FILE, "rb") as f:
        salt = f.read(16)
        encrypted_data = f.read()
    
    try:
        decrypted = FERNET_INSTANCE.decrypt(encrypted_data)
        return json.loads(decrypted.decode())
    except Exception:
        return {}


def save_secrets(secrets: Dict[str, str]):
    if not FERNET_INSTANCE:
        raise HTTPException(status_code=503, detail="Encryption not initialized")
    
    encrypted = FERNET_INSTANCE.encrypt(json.dumps(secrets).encode())
    
    with open(SECRETS_FILE, "wb") as f:
        with open(SECRETS_FILE, "rb") as rf:
            salt = rf.read(16)
        f.write(salt)
        f.write(encrypted)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": "cronos", "timestamp": datetime.now().isoformat()}


@app.get("/ping")
async def ping():
    return {"pong": True}


@app.post("/init")
async def init_master_password(request: MasterPasswordRequest):
    """Инициализация мастер-пароля"""
    try:
        init_encryption(request.password)
        return {"status": "success", "message": "Master password set"}
    except Exception as e:
        logger.error(f"Init error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/store")
async def store_secret(request: SecretRequest):
    """Сохранить секрет"""
    if not FERNET_INSTANCE:
        raise HTTPException(status_code=503, detail="Initialize master password first")
    
    secrets = load_secrets()
    secrets[request.key] = request.value
    save_secrets(secrets)
    
    return {"status": "success", "key": request.key}


@app.post("/get")
async def get_secret(request: SecretGetRequest):
    """Получить секрет"""
    if not FERNET_INSTANCE:
        raise HTTPException(status_code=503, detail="Initialize master password first")
    
    secrets = load_secrets()
    value = secrets.get(request.key)
    
    if value is None:
        raise HTTPException(status_code=404, detail="Secret not found")
    
    return {"key": request.key, "value": value}


@app.delete("/delete/{key}")
async def delete_secret(key: str):
    """Удалить секрет"""
    if not FERNET_INSTANCE:
        raise HTTPException(status_code=503, detail="Initialize master password first")
    
    secrets = load_secrets()
    if key in secrets:
        del secrets[key]
        save_secrets(secrets)
        return {"status": "success", "key": key}
    
    raise HTTPException(status_code=404, detail="Secret not found")


@app.get("/list")
async def list_secrets():
    """Список всех ключей (без значений)"""
    if not FERNET_INSTANCE:
        raise HTTPException(status_code=503, detail="Initialize master password first")
    
    secrets = load_secrets()
    return {"keys": list(secrets.keys()), "count": len(secrets)}


def main():
    uvicorn.run(app, host="0.0.0.0", port=8004)


if __name__ == "__main__":
    main()
