import os
import json
import hashlib
from pathlib import Path
from typing import Optional

# Local storage directory for passwords
PASSWORDS_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp', 'passwords')

class LocalPasswordService:
    def __init__(self):
        self._ensure_passwords_dir()
    
    def _ensure_passwords_dir(self):
        """Ensure the passwords directory exists"""
        os.makedirs(PASSWORDS_DIR, exist_ok=True)
    
    def _generate_key(self, login_url: str, username: str) -> str:
        """Generate SHA256 hash key from login_url + username"""
        combined = f"{login_url}{username}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _get_file_path(self, organization_name: str) -> str:
        """Get the file path for storing passwords for an organization"""
        # Sanitize organization name for file system
        safe_org_name = "".join(c for c in organization_name if c.isalnum() or c in ('-', '_', '.')).lower()
        return os.path.join(PASSWORDS_DIR, f"{safe_org_name}.json")
    
    def _load_passwords(self, organization_name: str) -> dict:
        """Load passwords for an organization from local file"""
        file_path = self._get_file_path(organization_name)
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading passwords for {organization_name}: {e}")
            return {}
    
    def _save_passwords(self, organization_name: str, passwords: dict) -> bool:
        """Save passwords for an organization to local file"""
        file_path = self._get_file_path(organization_name)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(passwords, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving passwords for {organization_name}: {e}")
            return False
    
    async def save_password(self, organization_name: str, login_url: str, username: str, password: str) -> bool:
        """Save password locally"""
        try:
            key = self._generate_key(login_url, username)
            passwords = self._load_passwords(organization_name)
            
            passwords[key] = {
                "login_url": login_url,
                "username": username,
                "password": password
            }
            
            return self._save_passwords(organization_name, passwords)
        except Exception as e:
            print(f"Error saving password: {e}")
            return False
    
    async def get_password(self, organization_name: str, login_url: str, username: str) -> Optional[str]:
        """Retrieve password from local storage"""
        try:
            key = self._generate_key(login_url, username)
            passwords = self._load_passwords(organization_name)
            
            if key in passwords:
                return passwords[key]["password"]
            return None
        except Exception as e:
            print(f"Error retrieving password: {e}")
            return None
