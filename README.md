# OPSEC Toolkit

A small toolkit for operational security utilities: password/passphrase generation, compartmentalized identities, and metadata stripping from media files.

This repo is a developer-oriented snapshot (work-in-progress). It is intended to be self-hosted.

## Goals
- Small, focused feature set: Password generation, Identity compartmentalization, Metadata stripping.
- Privacy-first defaults: minimal logging, encrypted storage options, and strong deletion semantics.
- Easy to self-host and extend.

## Quickstart (development)

1. Create a virtualenv and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure environment (see `.env.example`) and run the app:

```bash
cp .env.example .env
# edit .env to set SECRET_KEY and DATA_DIR
python3 app.py
```

3. Visit `http://localhost:5000`.

## Production notes
- Do NOT run with `debug=True` in production. Use a WSGI server such as `gunicorn` and put nginx or similar in front for TLS termination.
- Example:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

- Ensure `DATA_DIR` is on an encrypted disk if storing sensitive data.
- Provide a reverse proxy, TLS (Let's Encrypt), rate limiting and monitoring.

## Docker quickstart

Build and run with Docker / docker-compose:

```bash
docker build -t opsec-toolkit .
docker run --env-file .env -p 5000:5000 opsec-toolkit
# or with docker-compose
docker-compose up --build -d
```

Set `DATA_DIR` in `.env` to `/data` (docker-compose binds a `data` volume).

### Production Docker notes

- Build and run (example):

```bash
# Build image
docker build -t obscura-opsec .

# Run with docker-compose (reads .env)
docker-compose up -d --build
```

- Ensure you set `IDENTITIES_DIR=/data/opsec` in `.env` so identities are persisted to the `data` volume.
- Provide `IDENTITIES_FERNET_KEY` or `SECRET_KEY` and consider `ENFORCE_ENCRYPTION=true` to store identities encrypted at rest.
- The container includes `ffmpeg` and `libmagic` for metadata processing. For document scrubbing you can install `mat2` on the host or extend the image.

### Troubleshooting

- If video stripping fails, ensure `ffmpeg` is available in the container logs. The Dockerfile installs `ffmpeg` in the image.
- Logs are written to the container stdout; use `docker-compose logs -f web` to follow.

## Generating keys and tokens

For privacy best-practices, set `API_TOKEN` and `IDENTITIES_FERNET_KEY` in your `.env` before running.

Generate a Fernet key:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Generate a strong API token (example):

```bash
openssl rand -hex 32
```

Set these values in `.env` (or your environment) and consider setting `ENFORCE_ENCRYPTION=true` to prevent plaintext identity storage.

## Examples

See `examples/call_api.py` for a small script that demonstrates how to call the protected identity endpoints using `API_TOKEN`.

```bash
# Run the example (you will be prompted for the token if not set):
python3 examples/call_api.py
```

## Privacy & deletion
- The app attempts to securely overwrite and delete temporary files after processing, but secure deletion cannot be guaranteed on SSDs, journaled filesystems, or if backups exist.
- When an identity is deleted, the application removes it from the local datastore; you should rotate any keys and ensure backups are purged where possible.
- The README and docs include recommended practices for hard-delete and key rotation.

## Dependencies
See `requirements.txt` for Python packages. Some features (video stripping) require external tools like `ffmpeg` and `mat2`.

## Contributing
Contributions welcome. Please open issues or pull requests. Add tests for new features and follow the coding style used in the repo.

## License
This project is licensed under the MIT License - see the `LICENSE` file for details.
