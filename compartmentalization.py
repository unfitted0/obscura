"""
Compartmentalization Module
Manage separate identities, aliases, and isolated operations.
"""

import json
import secrets
import string
import random
import os
import base64
import logging
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet
import hashlib

from password_generator import PasswordGenerator


# Word lists for generating realistic usernames
ADJECTIVES = [
    "Swift", "Shadow", "Silent", "Dark", "Bright", "Cold", "Wild", "Lone",
    "Ghost", "Cyber", "Neon", "Void", "Storm", "Frost", "Iron", "Steel",
    "Crimson", "Azure", "Onyx", "Silver", "Golden", "Raven", "Wolf", "Hawk",
    "Night", "Dawn", "Dusk", "Cosmic", "Quantum", "Nova", "Pixel", "Binary",
    "Stealth", "Phantom", "Mystic", "Cryptic", "Hidden", "Masked", "Veiled",
    "Rapid", "Apex", "Prime", "Alpha", "Omega", "Zero", "Null", "Void",
    "Electric", "Thunder", "Lightning", "Blaze", "Ember", "Ash", "Smoke"
]

NOUNS = [
    "Wolf", "Fox", "Hawk", "Raven", "Phoenix", "Dragon", "Tiger", "Panther",
    "Viper", "Cobra", "Falcon", "Eagle", "Bear", "Lion", "Shark", "Lynx",
    "Knight", "Ninja", "Samurai", "Ronin", "Hunter", "Ranger", "Scout", "Agent",
    "Cipher", "Code", "Byte", "Node", "Proxy", "Vector", "Matrix", "Core",
    "Blade", "Edge", "Storm", "Pulse", "Wave", "Flux", "Spark", "Bolt",
    "Specter", "Wraith", "Shade", "Spirit", "Ghost", "Reaper", "Walker", "Runner",
    "Mind", "Soul", "Heart", "Eye", "Hand", "Fist", "Claw", "Wing"
]

PREFIXES = [
    "The", "Mr", "Dr", "Sir", "Lord", "Agent", "Captain", "Chief", "Master", ""
]


class IdentityManager:
    """Manage multiple identities and aliases for compartmentalization."""
    
    def __init__(self, data_dir="~/.opsec"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.identities_file = self.data_dir / "identities.json"
        self.logger = logging.getLogger(__name__)

        self.fernet = None
        identities_key = os.environ.get('IDENTITIES_FERNET_KEY')
        if identities_key:
            try:
                key_bytes = identities_key.encode() if isinstance(identities_key, str) else identities_key
                self.fernet = Fernet(key_bytes)
            except Exception:
                try:
                    secret = os.environ.get('SECRET_KEY', '')
                    digest = hashlib.sha256(secret.encode()).digest()
                    key = base64.urlsafe_b64encode(digest)
                    self.fernet = Fernet(key)
                except Exception:
                    self.logger.warning('Failed to initialize Fernet key for identities; storing plaintext')
        else:
            secret = os.environ.get('SECRET_KEY')
            if secret:
                try:
                    digest = hashlib.sha256(secret.encode()).digest()
                    key = base64.urlsafe_b64encode(digest)
                    self.fernet = Fernet(key)
                except Exception:
                    self.logger.warning('Failed to derive Fernet key from SECRET_KEY; storing plaintext')

        self.identities = self._load_identities()
        self.password_gen = PasswordGenerator()
        enforce = os.environ.get('ENFORCE_ENCRYPTION', 'false').lower() in ('1', 'true', 'yes')
        if enforce and not self.fernet:
            raise RuntimeError('ENFORCE_ENCRYPTION is set but no IDENTITIES_FERNET_KEY or SECRET_KEY is configured')

    def _load_identities(self):
        if self.identities_file.exists():
            try:
                with open(self.identities_file, 'rb') as f:
                    data = f.read()
                if self.fernet:
                    try:
                        decrypted = self.fernet.decrypt(data)
                        return json.loads(decrypted.decode())
                    except Exception:
                        try:
                            return json.loads(data.decode())
                        except Exception:
                            return {}
                else:
                    return json.loads(data.decode())
            except:
                return {}
        return {}

    def _save_identities(self):
        json_data = json.dumps(self.identities, indent=2).encode()
        try:
            if self.fernet:
                payload = self.fernet.encrypt(json_data)
            else:
                payload = json_data
            tmp_path = self.identities_file.with_suffix('.tmp')
            with open(tmp_path, 'wb') as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.identities_file)
        except Exception as e:
            try:
                with open(self.identities_file, 'w') as f:
                    json.dump(self.identities, f, indent=2)
            except Exception:
                self.logger.error(f"Failed to save identities: {e}")

    def _secure_overwrite_file(self, path):
        try:
            if not path.exists():
                return
            size = path.stat().st_size
            if size <= 0:
                try:
                    path.unlink()
                except Exception:
                    pass
                return
            with open(path, 'r+b') as f:
                f.seek(0)
                chunk = 1024 * 1024
                written = 0
                while written < size:
                    to_write = min(chunk, size - written)
                    f.write(os.urandom(to_write))
                    written += to_write
                f.flush()
                os.fsync(f.fileno())
                f.truncate(0)
                f.flush()
                os.fsync(f.fileno())
            try:
                path.unlink()
            except Exception:
                pass
        except Exception:
            pass

    def generate_alias(self, style="word_combo", include_numbers=True):
        if isinstance(style, int):
            length = style
            chars = string.ascii_lowercase
            if include_numbers:
                chars += string.digits
            return ''.join(secrets.choice(chars) for _ in range(length))
        if style == "word_combo":
            adjective = secrets.choice(ADJECTIVES)
            noun = secrets.choice(NOUNS)
            if include_numbers:
                number = secrets.randbelow(1000)
                formats = [
                    f"{adjective}{noun}{number}",
                    f"{adjective}_{noun}{number}",
                    f"{adjective}{noun}_{number}",
                    f"{adjective.lower()}{noun}{number}",
                    f"{adjective}{noun.lower()}{number}",
                ]
                return secrets.choice(formats)
            else:
                formats = [
                    f"{adjective}{noun}",
                    f"{adjective}_{noun}",
                    f"{adjective.lower()}{noun}",
                ]
                return secrets.choice(formats)
        elif style == "simple":
            word = secrets.choice(NOUNS).lower()
            if include_numbers:
                number = secrets.randbelow(1000)
                return f"{word}{number}"
            return word
        else:
            chars = string.ascii_lowercase
            if include_numbers:
                chars += string.digits
            return ''.join(secrets.choice(chars) for _ in range(12))

    def create_identity(self, name, purpose="", auto_rotate=True, 
                       generate_password=True, password_length=20,
                       generate_passphrase=False, passphrase_words=5):
        identity = {
            "name": name,
            "purpose": purpose,
            "alias": self.generate_alias(),
            "email_prefix": self.generate_alias(8),
            "created": datetime.now().isoformat(),
            "last_used": None,
            "use_count": 0,
            "auto_rotate": auto_rotate,
            "notes": []
        }
        if generate_password:
            password = self.password_gen.generate_password(length=password_length)
            identity["password"] = password
            identity["password_strength"] = self.password_gen.get_strength(password)
        if generate_passphrase:
            identity["passphrase"] = self.password_gen.generate_passphrase(
                words=passphrase_words
            )
        self.identities[name] = identity
        self._save_identities()
        return identity

    def get_identity(self, name, increment_use=True):
        if name in self.identities:
            identity = self.identities[name]
            if increment_use:
                identity["last_used"] = datetime.now().isoformat()
                identity["use_count"] = identity.get("use_count", 0) + 1
                self._save_identities()
            return identity
        return None

    def rotate_identity(self, name, rotate_password=True):
        if name not in self.identities:
            return None
        identity = self.identities[name]
        old_alias = identity["alias"]
        identity["alias"] = self.generate_alias()
        identity["email_prefix"] = self.generate_alias(8)
        identity["last_rotated"] = datetime.now().isoformat()
        identity["previous_aliases"] = identity.get("previous_aliases", [])
        identity["previous_aliases"].append(old_alias)
        if rotate_password and "password" in identity:
            old_password = identity["password"]
            identity["password"] = self.password_gen.generate_password()
            identity["password_strength"] = self.password_gen.get_strength(identity["password"])
            identity["previous_passwords"] = identity.get("previous_passwords", [])
            identity["rotated_passwords_count"] = identity.get("rotated_passwords_count", 0) + 1
        if "passphrase" in identity:
            identity["passphrase"] = self.password_gen.generate_passphrase()
        self._save_identities()
        return identity

    def regenerate_password(self, name, password_length=20):
        if name not in self.identities:
            return None
        identity = self.identities[name]
        identity["password"] = self.password_gen.generate_password(length=password_length)
        identity["password_strength"] = self.password_gen.get_strength(identity["password"])
        identity["password_regenerated"] = datetime.now().isoformat()
        self._save_identities()
        return identity

    def add_passphrase(self, name, words=5):
        if name not in self.identities:
            return None
        identity = self.identities[name]
        identity["passphrase"] = self.password_gen.generate_passphrase(words=words)
        self._save_identities()
        return identity

    def burn_identity(self, name):
        if name in self.identities:
            del self.identities[name]
            self._save_identities()
            try:
                tmp_path = self.identities_file.with_suffix('.tmp')
                if tmp_path.exists():
                    self._secure_overwrite_file(tmp_path)
                if self.identities_file.exists():
                    self._secure_overwrite_file(self.identities_file)
            except Exception:
                pass
            return True
        return False

    def list_identities(self):
        return list(self.identities.keys())

    def get_identity_stats(self):
        if not self.identities:
            return {"total": 0, "total_uses": 0}
        stats = {
            "total": len(self.identities),
            "total_uses": sum(i.get("use_count", 0) for i in self.identities.values()),
            "identities": {}
        }
        for name, identity in self.identities.items():
            stats["identities"][name] = {
                "use_count": identity.get("use_count", 0),
                "created": identity.get("created"),
                "last_used": identity.get("last_used"),
                "has_password": "password" in identity,
                "has_passphrase": "passphrase" in identity
            }
        return stats

    def add_note(self, name, note):
        if name not in self.identities:
            return False
        self.identities[name]["notes"].append({
            "text": note,
            "added": datetime.now().isoformat()
        })
        self._save_identities()
        return True

    def update_purpose(self, name, purpose):
        if name not in self.identities:
            return False
        self.identities[name]["purpose"] = purpose
        self._save_identities()
        return True


class CompartmentalizationHelper:
    def __init__(self):
        self.password_gen = PasswordGenerator()
    @staticmethod
    def generate_mac_address():
        return ':'.join(f'{secrets.randbelow(256):02x}' for _ in range(6))
    @staticmethod
    def generate_operation_id():
        return secrets.token_hex(16)
    def generate_credentials_set(self, include_passphrase=False, username_style="word_combo"):
        adjective = secrets.choice(ADJECTIVES)
        noun = secrets.choice(NOUNS)
        number = secrets.randbelow(1000)
        if username_style == "word_combo":
            formats = [
                f"{adjective}{noun}{number}",
                f"{adjective}_{noun}{number}",
                f"{adjective.lower()}{noun}{number}",
            ]
            alias = secrets.choice(formats)
        elif username_style == "simple":
            alias = f"{noun.lower()}{number}"
        else:
            alias = ''.join(secrets.choice(string.ascii_lowercase + string.digits) 
                           for _ in range(12))
        email_prefix = f"{adjective.lower()}{noun.lower()}{number}"
        password = self.password_gen.generate_password()
        credentials = {
            "username": alias,
            "email_prefix": email_prefix,
            "password": password,
            "password_strength": self.password_gen.get_strength(password),
            "generated": datetime.now().isoformat()
        }
        if include_passphrase:
            credentials["passphrase"] = self.password_gen.generate_passphrase()
        return credentials
    @staticmethod
    def create_compartment_checklist(operation_name):
        return {
            "operation": operation_name,
            "created": datetime.now().isoformat(),
            "checklist": {
                "separate_device": False,
                "separate_network": False,
                "separate_identity": False,
                "vpn_tor_enabled": False,
                "metadata_stripped": False,
                "no_cross_contamination": False,
                "burn_after_use": False
            },
            "notes": []
        }
    @staticmethod
    def validate_compartmentalization(identity_name, operation_type):
        warnings = []
        recommendations = []
        if operation_type == "sensitive" and identity_name:
            recommendations.append("Use a dedicated identity for sensitive operations")
            recommendations.append("Consider using a separate device or VM")
            recommendations.append("Enable VPN/Tor routing")
            recommendations.append("Strip all metadata before sharing")
        return {
            "valid": len(warnings) == 0,
            "warnings": warnings,
            "recommendations": recommendations
        }
