"""
Encrypted Credential Vault Module
Securely store and manage credentials with encryption.
"""

import json
import base64
import hashlib
import secrets
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CredentialVault:
    """
    Encrypted storage for credentials.
    
    Security:
    - Uses PBKDF2-HMAC-SHA256 with 600,000 iterations (OWASP 2023 compliant)
    - Unique random salt (32 bytes) per vault, stored separately
    - Fernet (AES-128 in CBC mode) for symmetric encryption
    - Salt file prevents rainbow table attacks
    
    Future Consideration:
    - Argon2id would provide better resistance to GPU/ASIC attacks
    - Consider migration for new vaults if higher security is needed
    """
    
    def __init__(self, data_dir="~/.opsec"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vault_file = self.data_dir / "vault.enc"
        self.salt_file = self.data_dir / "vault.salt"
        self.fernet = None
        self.is_unlocked = False
    
    def _derive_key(self, master_password, salt):
        """
        Derive encryption key from master password.
        
        Uses PBKDF2-HMAC-SHA256 with 600,000 iterations (OWASP 2023 recommendation).
        Salt is unique per vault and stored separately.
        
        Args:
            master_password: Master password string
            salt: Salt bytes (32 bytes, randomly generated)
        
        Returns:
            bytes: Derived key (32 bytes, base64 encoded)
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=600000,  # OWASP 2023 recommendation (increased from 480k)
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        return key
    
    def _get_salt(self):
        """
        Get or create salt.
        
        Salt is stored in a separate file (vault.salt) and is cryptographically
        random (32 bytes). Each vault has a unique salt to prevent rainbow table attacks.
        
        Returns:
            bytes: 32-byte random salt
        """
        if self.salt_file.exists():
            with open(self.salt_file, 'rb') as f:
                return f.read()
        else:
            # Generate cryptographically secure random salt
            salt = secrets.token_bytes(32)  # 256 bits of entropy
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            return salt
    
    def is_initialized(self):
        """Check if vault has been initialized."""
        return self.vault_file.exists() and self.salt_file.exists()
    
    def initialize(self, master_password):
        """
        Initialize a new vault with master password.
        
        Args:
            master_password: Master password for the vault
        
        Returns:
            bool: True if successful
        """
        if self.is_initialized():
            return False, "Vault already initialized. Use 'unlock' instead."
        
        if len(master_password) < 8:
            return False, "Master password must be at least 8 characters."
        
        salt = self._get_salt()
        key = self._derive_key(master_password, salt)
        self.fernet = Fernet(key)
        self.is_unlocked = True
        
        # Create empty vault
        vault_data = {
            "created": datetime.now().isoformat(),
            "version": "1.0",
            "credentials": {}
        }
        
        self._save_vault(vault_data)
        return True, "Vault initialized successfully."
    
    def unlock(self, master_password):
        """
        Unlock the vault with master password.
        
        Args:
            master_password: Master password
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.is_initialized():
            return False, "Vault not initialized. Use 'init' first."
        
        salt = self._get_salt()
        key = self._derive_key(master_password, salt)
        self.fernet = Fernet(key)
        
        try:
            # Try to decrypt to verify password
            self._load_vault()
            self.is_unlocked = True
            return True, "Vault unlocked successfully."
        except Exception:
            self.fernet = None
            self.is_unlocked = False
            return False, "Invalid master password."
    
    def lock(self):
        """Lock the vault."""
        self.fernet = None
        self.is_unlocked = False
        return True, "Vault locked."
    
    def _load_vault(self):
        """Load and decrypt vault data."""
        if not self.fernet:
            raise Exception("Vault is locked.")
        
        with open(self.vault_file, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = self.fernet.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
    
    def _save_vault(self, vault_data):
        """Encrypt and save vault data."""
        if not self.fernet:
            raise Exception("Vault is locked.")
        
        json_data = json.dumps(vault_data, indent=2).encode()
        encrypted_data = self.fernet.encrypt(json_data)
        
        with open(self.vault_file, 'wb') as f:
            f.write(encrypted_data)
    
    def add_credential(self, identity_name, service, username=None, password=None, 
                      email=None, notes=None, extra_fields=None):
        """
        Add a credential to the vault.
        
        Args:
            identity_name: Name of the identity this credential belongs to
            service: Service name (e.g., "reddit", "twitter")
            username: Username for the service
            password: Password for the service
            email: Email used for the service
            notes: Additional notes
            extra_fields: Dict of additional fields
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.is_unlocked:
            return False, "Vault is locked. Unlock it first."
        
        vault_data = self._load_vault()
        
        if identity_name not in vault_data["credentials"]:
            vault_data["credentials"][identity_name] = []
        
        credential = {
            "id": secrets.token_hex(8),
            "service": service,
            "username": username,
            "password": password,
            "email": email,
            "notes": notes,
            "extra_fields": extra_fields or {},
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat()
        }
        
        vault_data["credentials"][identity_name].append(credential)
        self._save_vault(vault_data)
        
        return True, f"Credential added for {service} under identity '{identity_name}'."
    
    def get_credentials(self, identity_name):
        """
        Get all credentials for an identity.
        
        Args:
            identity_name: Name of the identity
        
        Returns:
            list: List of credentials
        """
        if not self.is_unlocked:
            return None, "Vault is locked. Unlock it first."
        
        vault_data = self._load_vault()
        credentials = vault_data["credentials"].get(identity_name, [])
        
        return credentials, f"Found {len(credentials)} credential(s) for '{identity_name}'."
    
    def get_credential_by_service(self, identity_name, service):
        """
        Get a specific credential by service name.
        
        Args:
            identity_name: Name of the identity
            service: Service name
        
        Returns:
            dict: Credential or None
        """
        if not self.is_unlocked:
            return None, "Vault is locked. Unlock it first."
        
        vault_data = self._load_vault()
        credentials = vault_data["credentials"].get(identity_name, [])
        
        for cred in credentials:
            if cred["service"].lower() == service.lower():
                return cred, f"Found credential for {service}."
        
        return None, f"No credential found for {service}."
    
    def update_credential(self, identity_name, credential_id, **updates):
        """
        Update a credential.
        
        Args:
            identity_name: Name of the identity
            credential_id: ID of the credential to update
            **updates: Fields to update
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.is_unlocked:
            return False, "Vault is locked. Unlock it first."
        
        vault_data = self._load_vault()
        credentials = vault_data["credentials"].get(identity_name, [])
        
        for cred in credentials:
            if cred["id"] == credential_id:
                for key, value in updates.items():
                    if key in cred and key not in ["id", "created"]:
                        cred[key] = value
                cred["modified"] = datetime.now().isoformat()
                self._save_vault(vault_data)
                return True, "Credential updated successfully."
        
        return False, "Credential not found."
    
    def delete_credential(self, identity_name, credential_id):
        """
        Delete a credential.
        
        Args:
            identity_name: Name of the identity
            credential_id: ID of the credential to delete
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.is_unlocked:
            return False, "Vault is locked. Unlock it first."
        
        vault_data = self._load_vault()
        credentials = vault_data["credentials"].get(identity_name, [])
        
        for i, cred in enumerate(credentials):
            if cred["id"] == credential_id:
                del credentials[i]
                self._save_vault(vault_data)
                return True, "Credential deleted successfully."
        
        return False, "Credential not found."
    
    def delete_identity_credentials(self, identity_name):
        """
        Delete all credentials for an identity.
        
        Args:
            identity_name: Name of the identity
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.is_unlocked:
            return False, "Vault is locked. Unlock it first."
        
        vault_data = self._load_vault()
        
        if identity_name in vault_data["credentials"]:
            count = len(vault_data["credentials"][identity_name])
            del vault_data["credentials"][identity_name]
            self._save_vault(vault_data)
            return True, f"Deleted {count} credential(s) for identity '{identity_name}'."
        
        return False, f"No credentials found for identity '{identity_name}'."
    
    def list_identities(self):
        """
        List all identities with credentials.
        
        Returns:
            list: List of identity names
        """
        if not self.is_unlocked:
            return None, "Vault is locked. Unlock it first."
        
        vault_data = self._load_vault()
        identities = list(vault_data["credentials"].keys())
        
        return identities, f"Found {len(identities)} identity/identities with credentials."
    
    def list_all_credentials(self):
        """
        List all credentials (summary only, no passwords).
        
        Returns:
            dict: Summary of all credentials
        """
        if not self.is_unlocked:
            return None, "Vault is locked. Unlock it first."
        
        vault_data = self._load_vault()
        summary = {}
        
        for identity_name, credentials in vault_data["credentials"].items():
            summary[identity_name] = [
                {
                    "id": cred["id"],
                    "service": cred["service"],
                    "username": cred["username"],
                    "email": cred["email"],
                    "created": cred["created"]
                }
                for cred in credentials
            ]
        
        return summary, "Credential summary retrieved."
    
    def export_vault(self, output_path, export_password=None):
        """
        Export vault to encrypted file.
        
        Args:
            output_path: Path for export file
            export_password: Optional separate password for export
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.is_unlocked:
            return False, "Vault is locked. Unlock it first."
        
        vault_data = self._load_vault()
        
        if export_password:
            # Use different password for export
            salt = secrets.token_bytes(32)
            key = self._derive_key(export_password, salt)
            export_fernet = Fernet(key)
            
            export_data = {
                "salt": base64.b64encode(salt).decode(),
                "data": base64.b64encode(
                    export_fernet.encrypt(json.dumps(vault_data).encode())
                ).decode()
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f)
        else:
            # Use same encryption as vault
            with open(output_path, 'wb') as f:
                f.write(self.fernet.encrypt(json.dumps(vault_data).encode()))
        
        return True, f"Vault exported to {output_path}."
    
    def import_vault(self, import_path, import_password=None, merge=False):
        """
        Import vault from encrypted file.
        
        Args:
            import_path: Path to import file
            import_password: Password for the import file
            merge: Merge with existing vault instead of replacing
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.is_unlocked:
            return False, "Vault is locked. Unlock it first."
        
        try:
            with open(import_path, 'r') as f:
                content = f.read()
            
            # Check if it's JSON (password-protected export)
            try:
                export_data = json.loads(content)
                if "salt" in export_data and "data" in export_data:
                    if not import_password:
                        return False, "Import password required for this export file."
                    
                    salt = base64.b64decode(export_data["salt"])
                    key = self._derive_key(import_password, salt)
                    import_fernet = Fernet(key)
                    
                    encrypted_data = base64.b64decode(export_data["data"])
                    vault_data = json.loads(import_fernet.decrypt(encrypted_data).decode())
            except json.JSONDecodeError:
                # Binary encrypted file (same password as vault)
                with open(import_path, 'rb') as f:
                    encrypted_data = f.read()
                vault_data = json.loads(self.fernet.decrypt(encrypted_data).decode())
            
            if merge:
                current_vault = self._load_vault()
                for identity_name, credentials in vault_data["credentials"].items():
                    if identity_name not in current_vault["credentials"]:
                        current_vault["credentials"][identity_name] = []
                    current_vault["credentials"][identity_name].extend(credentials)
                self._save_vault(current_vault)
                return True, "Vault merged successfully."
            else:
                self._save_vault(vault_data)
                return True, "Vault imported successfully."
                
        except Exception as e:
            return False, f"Import failed: {str(e)}"
    
    def change_master_password(self, current_password, new_password):
        """
        Change the master password.
        
        Args:
            current_password: Current master password
            new_password: New master password
        
        Returns:
            tuple: (success: bool, message: str)
        """
        # Verify current password
        success, message = self.unlock(current_password)
        if not success:
            return False, "Current password is incorrect."
        
        if len(new_password) < 8:
            return False, "New password must be at least 8 characters."
        
        # Load vault data with current password
        vault_data = self._load_vault()
        
        # Generate new salt and key
        new_salt = secrets.token_bytes(32)
        new_key = self._derive_key(new_password, new_salt)
        
        # Update salt file
        with open(self.salt_file, 'wb') as f:
            f.write(new_salt)
        
        # Re-encrypt vault with new key
        self.fernet = Fernet(new_key)
        self._save_vault(vault_data)
        
        return True, "Master password changed successfully."
    
    def get_vault_stats(self):
        """
        Get vault statistics.
        
        Returns:
            dict: Vault statistics
        """
        if not self.is_unlocked:
            return None, "Vault is locked. Unlock it first."
        
        vault_data = self._load_vault()
        
        total_credentials = sum(
            len(creds) for creds in vault_data["credentials"].values()
        )
        
        services = set()
        for creds in vault_data["credentials"].values():
            for cred in creds:
                services.add(cred["service"].lower())
        
        return {
            "created": vault_data.get("created"),
            "version": vault_data.get("version"),
            "total_identities": len(vault_data["credentials"]),
            "total_credentials": total_credentials,
            "unique_services": len(services),
            "services": list(services)
        }, "Vault statistics retrieved."

