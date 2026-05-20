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
    # This already prevents '../' by stripping everything but a-z0-9 and hyphens
    norm = re.sub(r'[^a-z0-9]', '-', name.lower()).strip('-')
    if not norm:
        raise HTTPException(status_code=400, detail="Invalid name")
    return norm

def save_file(content: bytes, path: str):
    # Absolute path of the data directory
    base_dir = os.path.abspath("data")
    # Absolute path of the target file
    target_path = os.path.abspath(path)
    
    # Ensure the target path is inside the base data directory
    if not target_path.startswith(base_dir):
        raise HTTPException(status_code=400, detail="Invalid file path")
        
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "wb") as f:
        f.write(content)
