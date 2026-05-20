import os
import re
from fastapi import HTTPException, Query, Depends

def get_token():
    try:
        with open("secrets/token", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def verify_token(token: str = Query(...)):
    expected = get_token()
    if not expected or token != expected:
        raise HTTPException(status_code=403, detail="Invalid token")
    return token

def normalise_name(name: str):
    # Lowercase and replace non-alphanumeric with hyphens
    return re.sub(r'[^a-z0-9]', '-', name.lower()).strip('-')

def save_file(content: bytes, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)
