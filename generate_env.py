#!/usr/bin/env python3
"""
Generate .env file with secure keys for Obscura
Run this once during initial setup
"""

import secrets
from cryptography.fernet import Fernet
import datetime
import os


def generate_secret_key():
    """Generate a secure Flask SECRET_KEY"""
    return secrets.token_hex(32)


def generate_fernet_key():
    """Generate a Fernet encryption key"""
    return Fernet.generate_key().decode()


def create_env_file():
    """Create .env file with generated keys"""

    secret_key = generate_secret_key()
    fernet_key = generate_fernet_key()

    env_content = f"""# Obscura Environment Configuration
# Generated on: {datetime.datetime.now().isoformat()}

# Flask secret key (for sessions, CSRF, etc.)
SECRET_KEY={secret_key}

# Fernet key for encrypting stored identities
IDENTITIES_FERNET_KEY={fernet_key}

# Data directory (where identities are stored)
IDENTITIES_DIR=./data

# Flask environment (production or development)
FLASK_ENV=production

# Optional: Set to 'true' to enable debug mode (NOT for production!)
# FLASK_DEBUG=false

# Optional: Host and port (container may override)
# FLASK_HOST=0.0.0.0
# FLASK_PORT=8000
"""

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    with open('.env', 'w') as f:
        f.write(env_content)

    print("✅ Generated .env file with secure keys")
    print("\n🔐 Security Notes:")
    print("   - Keep .env file private (already in .gitignore)")
    print("   - These keys are unique to your installation")
    print("   - IDENTITIES_FERNET_KEY encrypts your stored identities")
    print("   - SECRET_KEY secures Flask sessions")
    print("\n📁 Data Directory:")
    print("   - Identities will be stored in: ./data")
    print("   - This directory was created automatically")
    print("\n🚀 Next Steps:")
    print("   1. Review .env file")
    print("   2. Run: docker-compose up -d --build")
    print("   3. Access: http://localhost:8000 (or the port you configured)")


if __name__ == "__main__":
    try:
        create_env_file()
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
