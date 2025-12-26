# Obscura

**Privacy-first identity compartmentalization toolkit**

Obscura helps you create and manage separate online identities, generate secure credentials, and strip metadata from files before sharing.

[![CI](https://github.com/unfitted0/obscura/actions/workflows/ci.yml/badge.svg)](https://github.com/unfitted0/obscura/actions)

## Features

### 🎭 **Identity Management**
- Create compartmentalized identities for different purposes
- Auto-generate usernames, email prefixes, and passwords
- Store encrypted locally using Fernet (AES-128)
- Track usage and rotate identities when needed

### ⚡ **Credential Generation**
- Strong passwords (customizable length)
- Memorable passphrases (multiple words)
- Numeric PINs
- Strength analysis and entropy calculation

### 🧹 **Metadata Stripper**
- Remove EXIF data from images (JPG, PNG, TIFF)
- Strip tags from audio files (MP3, FLAC, OGG)
- Clean video metadata (MP4, AVI, MOV)
- Batch processing support

### ✅ **OPSEC Checklist**
- Pre-operation security checklist
- VPN/Tor verification reminders
- Identity separation checks
- Device security validation

## Why Obscura?

**Traditional password managers** store credentials but don't help you create compartmentalized identities.

**Obscura** helps you maintain separate personas:
- Different username for each service
- Unique email alias per identity
- Purpose-based organization

**Use cases:**
- Privacy advocates
- Security researchers
- Journalists protecting sources
- Anyone who values compartmentalization

## Quick Start

### Option 1: Docker (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/<OWNER>/obscura.git
cd obscura

# 2. Generate environment config
python3 generate_env.py

# 3. Start the container
docker-compose up -d --build

# 4. Access the UI
open http://localhost:8000
```

### Option 2: Local Development

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Generate environment config
python3 generate_env.py

# 3. Run the Flask app
python3 app.py

# 4. Access the UI
open http://localhost:8000
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
SECRET_KEY=<flask-secret-key>
IDENTITIES_FERNET_KEY=<fernet-encryption-key>

# Optional
IDENTITIES_DIR=./data              # Data storage location
FLASK_ENV=production              # production or development
FLASK_HOST=0.0.0.0               # Bind address
FLASK_PORT=8000                  # Port number
```

**Generate secure keys:**
```bash
python3 generate_env.py
```

### Data Persistence

When using Docker, identities are stored in `./data` (mounted volume).

**Backup your data:**
```bash
# Backup
tar -czf obscura-backup-$(date +%Y%m%d).tar.gz data/

# Restore
tar -xzf obscura-backup-YYYYMMDD.tar.gz
```

## Usage Examples

### Creating an Identity

1. Navigate to **Identities** tab
2. Click **+ New Identity**
3. Enter name and purpose
4. Enable password/passphrase generation
5. Click **Create Identity**

Your new identity includes:
- Auto-generated username/alias
- Email prefix for aliasing services
- Secure password (optional)
- Memorable passphrase (optional)

### Stripping Metadata

1. Navigate to **Metadata** tab
2. Drag and drop files (or click to browse)
3. Click **🧹 Strip All Metadata**
4. Download cleaned files

**Supported formats:**
- Images: JPG, PNG, TIFF, WEBP
- Audio: MP3, FLAC, OGG, M4A, WAV
- Video: MP4, AVI, MOV, MKV, WEBM

### Using the Checklist

1. Navigate to **Checklist** tab
2. Review OPSEC items before sensitive operations
3. Check off completed items
4. Track readiness percentage

## Security

### Encryption

- **Identity data:** Encrypted with Fernet (AES-128 CBC + HMAC)
- **Key derivation:** PBKDF2-HMAC-SHA256 (600k iterations)
- **Storage:** Local only, no cloud sync
- **Metadata:** Securely deleted after processing

### Threat Model

**Obscura protects against:**
- ✅ Credential reuse across services
- ✅ Identity linking through metadata
- ✅ Tracking via consistent usernames/emails
- ✅ Data leaks from unencrypted storage

**Obscura does NOT protect against:**
- ❌ Compromised device (use disk encryption)
- ❌ Keyloggers (use secure input methods)
- ❌ Network surveillance (use VPN/Tor)
- ❌ Browser fingerprinting (use Tor Browser)

### Best Practices

1. **Use with VPN/Tor** for anonymity
2. **Enable disk encryption** on your device
3. **Regular backups** of `./data` directory
4. **Rotate identities** periodically
5. **Strip metadata** before sharing any files

## Development

### Running Tests

```bash
# Run test suite (when implemented)
pytest tests/

# Lint code
flake8 app.py

# Type checking
mypy app.py
```

### Project Structure

```
obscura/
├── app.py                  # Flask backend
├── templates/
│   └── index.html         # Web UI
├── opsec_toolkit/         # Core modules
│   ├── password_generator.py
│   ├── compartmentalization.py
│   ├── credential_vault.py
│   └── metadata_stripper.py
├── docker-compose.yml     # Docker setup
├── Dockerfile            # Container definition
├── requirements.txt      # Python dependencies
└── .github/
	└── workflows/
		└── ci.yml       # GitHub Actions CI
```

## Roadmap

### Near-term
- [ ] Email alias integration (SimpleLogin, AnonAddy)
- [ ] Browser extension for quick access
- [ ] Import/export functionality
- [ ] Mobile-responsive improvements

### Long-term
- [ ] Desktop app (Electron wrapper)
- [ ] Multi-user support (teams)
- [ ] Biometric unlock (optional)
- [ ] Encrypted cloud sync (optional)

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests (if applicable)
5. Submit a pull request

**Code style:**
- Follow PEP 8 for Python
- Use meaningful variable names
- Add comments for complex logic
- Keep functions focused and small

## License

MIT License - see [LICENSE](LICENSE) file

## Disclaimer

This tool is for educational and legitimate privacy purposes only. Users are responsible for complying with applicable laws and service terms of use.

**Not a substitute for:**
- Professional security audits
- Legal advice
- Operational security training

## Support

- 🐛 **Issues:** [GitHub Issues](https://github.com/unfitted0/obscura/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/unfitted0/obscura/discussions)
- 📧 **Contact:** [Your preferred contact method]

## Acknowledgments

Built as a learning project to explore:
- Identity compartmentalization
- Cryptography best practices
- Privacy-focused design
- Self-hosted security tools

Inspired by the privacy and security communities on Reddit, Hacker News, and beyond.

---

**⭐ If you find Obscura useful, please star the repo!**

Made with ❤️ for privacy advocates everywhere.


