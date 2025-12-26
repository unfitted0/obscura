"""
OPSEC Toolkit - Web UI
Flask web interface for the OPSEC Toolkit
"""

try:
    from flask import Flask, render_template, jsonify, request, send_file, after_this_request
    HAVE_FLASK = True
except Exception:
    HAVE_FLASK = False
import sys
import os
import tempfile
import io
import shutil
import atexit
import time
import logging
from functools import wraps

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if HAVE_FLASK:
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload
else:
    # Create a minimal dummy 'app' object so decorators like @app.route
    # do not fail at import time when Flask is not installed. This keeps
    # the module importable and allows the fallback static server in
    # __main__ to run.
    class _DummyApp:
        def route(self, *args, **kwargs):
            def _decorator(f):
                return f
            return _decorator
        def __getattr__(self, name):
            # Provide harmless placeholders for attributes used during import.
            def _noop(*a, **k):
                raise RuntimeError('Flask not available in this environment')
            return _noop
    app = _DummyApp()

# Initialize components with error handling
logger.info("Initializing OPSEC Toolkit components...")
try:
    # Use local copy modules for this distribution
    from password_generator_copy import PasswordGenerator
    password_gen = PasswordGenerator()
    logger.info("✓ PasswordGenerator initialized")
except Exception as e:
    logger.error(f"✗ Failed to initialize PasswordGenerator: {e}")
    password_gen = None

try:
    from compartmentalization_copy import IdentityManager, CompartmentalizationHelper
    # Allow containerized deployments to override the identities storage location
    identities_dir = os.environ.get('IDENTITIES_DIR', '~/.opsec')
    identity_manager = IdentityManager(data_dir=identities_dir)
    helper = CompartmentalizationHelper()
    logger.info("✓ IdentityManager and CompartmentalizationHelper initialized")
except Exception as e:
    logger.error(f"✗ Failed to initialize Identity components: {e}")
    identity_manager = None
    helper = None

try:
    from metadata_stripper_copy import MetadataStripper
    metadata_stripper = MetadataStripper()
    logger.info("✓ MetadataStripper initialized")
except Exception as e:
    logger.error(f"✗ Failed to initialize MetadataStripper: {e}")
    metadata_stripper = None

# Noise generator and digital hygiene auditor are not initialized in this build
noise_generator = None
hygiene_auditor = None

logger.info("Component initialization complete.")

# API auth removed for self-hosted usage: decorator is a no-op
def require_api_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

# Lazy initialization of temp directory (created on first use)
METADATA_TEMP_DIR = None
_cleanup_registered = False

def get_metadata_temp_dir():
    """Get or create secure temp directory for metadata stripping."""
    global METADATA_TEMP_DIR, _cleanup_registered
    if METADATA_TEMP_DIR is None:
        try:
            METADATA_TEMP_DIR = tempfile.mkdtemp(prefix='opsec_metadata_')
            os.chmod(METADATA_TEMP_DIR, 0o700)  # Restrict permissions
            if not _cleanup_registered:
                atexit.register(cleanup_temp_dir)
                _cleanup_registered = True
            logger.info(f"Created metadata temp directory: {METADATA_TEMP_DIR}")
        except Exception as e:
            logger.warning(f"Failed to create custom temp dir, using system temp: {e}")
            # Fallback to system temp if custom temp dir fails
            METADATA_TEMP_DIR = tempfile.gettempdir()
    return METADATA_TEMP_DIR

def secure_delete_file(filepath):
    """Attempt to overwrite a file then delete it (best-effort).

    Notes:
    - This is best-effort. Secure deletion is not guaranteed on SSDs,
      journaled filesystems, or if backups/snapshots exist.
    """
    try:
        if not filepath:
            return
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size > 0:
                try:
                    with open(filepath, 'r+b') as f:
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
                except Exception:
                    # If overwrite fails, continue to attempt unlink
                    pass
            try:
                os.unlink(filepath)
            except Exception:
                pass
    except Exception:
        # Last-resort: try a normal delete
        try:
            if filepath and os.path.exists(filepath):
                os.unlink(filepath)
        except Exception:
            pass

def cleanup_temp_dir():
    """Clean up temporary metadata directory on exit."""
    global METADATA_TEMP_DIR
    try:
        if METADATA_TEMP_DIR and os.path.exists(METADATA_TEMP_DIR):
            shutil.rmtree(METADATA_TEMP_DIR)
    except Exception:
        pass

@app.route('/')
def index():
    """Main page with identity generator"""
    return render_template('index.html')
@app.route('/test-image')
def test_image():
    """Download test image with metadata for testing the stripper"""
    test_file = os.path.join(app.root_path, 'templates', 'test_image_with_metadata.jpg')
    if os.path.exists(test_file):
        return send_file(test_file, as_attachment=True, download_name='test_image_WITH_METADATA.jpg')
    return jsonify({'error': 'Test image not found'}), 404

# -- Re-enabled API endpoints (no auth) so the UI works locally --
@app.route('/api/health', methods=['GET'])
def health_check():
    components = {
        'password_gen': password_gen is not None,
        'identity_manager': identity_manager is not None,
        'helper': helper is not None,
        'metadata_stripper': metadata_stripper is not None,
    }
    all_ok = all(components.values())
    return jsonify({
        'status': 'healthy' if all_ok else 'degraded',
        'components': components
    }), 200 if all_ok else 503


@app.route('/api/generate', methods=['POST'])
def generate_credentials():
    if helper is None:
        return jsonify({'success': False, 'error': 'CompartmentalizationHelper not available'}), 503
    data = request.json or {}
    include_passphrase = data.get('include_passphrase', False)
    password_length = data.get('password_length', 20)
    passphrase_words = data.get('passphrase_words', 5)
    creds = helper.generate_credentials_set(include_passphrase=include_passphrase)
    if password_length != 20 and password_gen is not None:
        creds['password'] = password_gen.generate_password(length=password_length)
        creds['password_strength'] = password_gen.get_strength(creds['password'])
    if include_passphrase and passphrase_words != 5 and password_gen is not None:
        creds['passphrase'] = password_gen.generate_passphrase(words=passphrase_words)
    return jsonify({'success': True, 'credentials': creds})


@app.route('/api/generate-password', methods=['POST'])
def generate_password():
    if password_gen is None:
        return jsonify({'success': False, 'error': 'PasswordGenerator not available'}), 503
    data = request.json or {}
    length = data.get('length', 20)
    include_symbols = data.get('include_symbols', True)
    password = password_gen.generate_password(length=length, symbols=include_symbols)
    strength = password_gen.get_strength(password)
    return jsonify({'success': True, 'password': password, 'strength': strength})


@app.route('/api/generate-passphrase', methods=['POST'])
def generate_passphrase():
    if password_gen is None:
        return jsonify({'success': False, 'error': 'PasswordGenerator not available'}), 503
    data = request.json or {}
    words = data.get('words', 5)
    separator = data.get('separator', '-')
    passphrase = password_gen.generate_passphrase(words=words, separator=separator)
    return jsonify({'success': True, 'passphrase': passphrase})


@app.route('/api/identities', methods=['GET'])
def list_identities():
    if identity_manager is None:
        return jsonify({'success': False, 'error': 'IdentityManager not available'}), 503
    identity_names = identity_manager.list_identities()
    include_details = request.args.get('details', 'false').lower() == 'true'
    if include_details:
        identities = {}
        for name in identity_names:
            identity = identity_manager.get_identity(name, increment_use=False)
            if identity:
                identities[name] = identity
        return jsonify({'success': True, 'identities': identities, 'count': len(identity_names)})
    return jsonify({'success': True, 'identities': identity_names, 'count': len(identity_names)})


@app.route('/api/identity/create', methods=['POST'])
def create_identity():
    if identity_manager is None:
        return jsonify({'success': False, 'error': 'IdentityManager not available'}), 503
    data = request.json or {}
    name = data.get('name')
    if not name:
        return jsonify({'success': False, 'error': 'Name is required'}), 400
    existing = identity_manager.get_identity(name, increment_use=False)
    if existing:
        return jsonify({'success': False, 'error': 'Identity with this name already exists'}), 400
    purpose = data.get('purpose', '')
    generate_password_flag = data.get('generate_password', True)
    generate_passphrase_flag = data.get('generate_passphrase', False)
    password_length = data.get('password_length', 20)
    passphrase_words = data.get('passphrase_words', 5)
    identity = identity_manager.create_identity(
        name=name,
        purpose=purpose,
        generate_password=generate_password_flag,
        password_length=password_length,
        generate_passphrase=generate_passphrase_flag,
        passphrase_words=passphrase_words
    )
    return jsonify({'success': True, 'identity': identity})


@app.route('/api/identity/<name>', methods=['GET'])
def get_identity(name):
    if identity_manager is None:
        return jsonify({'success': False, 'error': 'IdentityManager not available'}), 503
    identity = identity_manager.get_identity(name, increment_use=False)
    if not identity:
        return jsonify({'success': False, 'error': 'Identity not found'}), 404
    return jsonify({'success': True, 'identity': identity})


@app.route('/api/identity/<name>/rotate', methods=['POST'])
def rotate_identity(name):
    if identity_manager is None:
        return jsonify({'success': False, 'error': 'IdentityManager not available'}), 503
    identity = identity_manager.rotate_identity(name)
    if not identity:
        return jsonify({'success': False, 'error': 'Identity not found'}), 404
    return jsonify({'success': True, 'identity': identity})


@app.route('/api/identity/<name>/burn', methods=['DELETE'])
def burn_identity(name):
    if identity_manager is None:
        return jsonify({'success': False, 'error': 'IdentityManager not available'}), 503
    success = identity_manager.burn_identity(name)
    if not success:
        return jsonify({'success': False, 'error': 'Identity not found'}), 404
    return jsonify({'success': True, 'message': f'Identity {name} burned'})
    tmp_path = None
    output_path = None
    
    try:
        # Use secure temp directory
        tmp_path = os.path.join(get_metadata_temp_dir(), f"tmp_{int(time.time() * 1000000)}{ext}")
        file.save(tmp_path)
        os.chmod(tmp_path, 0o600)  # Restrict file permissions
        
        output_path = tmp_path  # Default to same file (in-place strip)
        
        if metadata_stripper is None:
            secure_delete_file(tmp_path)
            return jsonify({'success': False, 'error': 'MetadataStripper not available'}), 503
        
        # Determine file type and strip metadata
        if ext in metadata_stripper.supported_image_formats:
            # For images, create a separate output file
            output_path = os.path.join(get_metadata_temp_dir(), f"clean_{int(time.time() * 1000000)}{ext}")
            success, message = metadata_stripper.strip_image_metadata(tmp_path, output_path)
        elif ext in metadata_stripper.supported_audio_formats:
            success, message = metadata_stripper.strip_audio_metadata(tmp_path)
            output_path = tmp_path  # Audio is stripped in-place
        elif ext in metadata_stripper.supported_video_formats:
            output_path = os.path.join(get_metadata_temp_dir(), f"clean_{int(time.time() * 1000000)}{ext}")
            success, message = metadata_stripper.strip_video_metadata(tmp_path, output_path)
        else:
            secure_delete_file(tmp_path)
            return jsonify({'success': False, 'error': f'Unsupported file type: {ext}'}), 400
        
        if not success:
            # Clean up and return error
            if tmp_path and os.path.exists(tmp_path):
                secure_delete_file(tmp_path)
            if output_path and output_path != tmp_path and os.path.exists(output_path):
                secure_delete_file(output_path)
            return jsonify({'success': False, 'error': message}), 500
        
        # Return the cleaned file for download
        clean_filename = f"{name}_clean{ext}"
        
        # Stream the cleaned file to the client and remove temp files after response
        @after_this_request
        def _cleanup(response):
            try:
                if tmp_path and os.path.exists(tmp_path):
                    secure_delete_file(tmp_path)
                if output_path and output_path != tmp_path and os.path.exists(output_path):
                    secure_delete_file(output_path)
            except Exception:
                pass
            return response

        return send_file(
            str(output_path),
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=clean_filename
        )
        
    except Exception as e:
        # Ensure cleanup on error
        if tmp_path and os.path.exists(tmp_path):
            secure_delete_file(tmp_path)
        if output_path and output_path != tmp_path and os.path.exists(output_path):
            secure_delete_file(output_path)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/metadata/strip-info', methods=['POST'])
def strip_metadata_info():
    """Strip metadata and return info (without file download) - uses secure temp directory"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    ext = os.path.splitext(file.filename)[1].lower()
    tmp_path = None
    output_path = None
    
    try:
        # Use secure temp directory
        tmp_path = os.path.join(get_metadata_temp_dir(), f"info_{int(time.time() * 1000000)}{ext}")
        file.save(tmp_path)
        os.chmod(tmp_path, 0o600)
        
        if metadata_stripper is None:
            secure_delete_file(tmp_path)
            return jsonify({'success': False, 'error': 'MetadataStripper not available'}), 503
        
        # Get metadata count before stripping
        before = metadata_stripper.inspect_metadata(tmp_path)
        before_count = len(before.get('metadata', {}))
        
        # Strip metadata
        if ext in metadata_stripper.supported_image_formats:
            success, message = metadata_stripper.strip_image_metadata(tmp_path)
        elif ext in metadata_stripper.supported_audio_formats:
            success, message = metadata_stripper.strip_audio_metadata(tmp_path)
        elif ext in metadata_stripper.supported_video_formats:
            output_path = os.path.join(get_metadata_temp_dir(), f"stripped_{int(time.time() * 1000000)}{ext}")
            success, message = metadata_stripper.strip_video_metadata(tmp_path, output_path)
            if success and output_path and os.path.exists(output_path):
                secure_delete_file(output_path)
        else:
            secure_delete_file(tmp_path)
            return jsonify({'success': False, 'error': f'Unsupported file type: {ext}'}), 400
        
        # Clean up temp file after inspecting
        secure_delete_file(tmp_path)

        return jsonify({
            'success': success,
            'message': message,
            'filename': file.filename,
            'metadata_removed': before_count
        })
        
    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            secure_delete_file(tmp_path)
        if output_path and os.path.exists(output_path):
            secure_delete_file(output_path)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/metadata/inspect', methods=['POST'])
def inspect_metadata():
    """Inspect metadata in uploaded file - uses secure temp directory"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    ext = os.path.splitext(file.filename)[1].lower()
    tmp_path = None
    
    try:
        # Use secure temp directory
        tmp_path = os.path.join(get_metadata_temp_dir(), f"inspect_{int(time.time() * 1000000)}{ext}")
        file.save(tmp_path)
        os.chmod(tmp_path, 0o600)
        
        if metadata_stripper is None:
            secure_delete_file(tmp_path)
            return jsonify({'success': False, 'error': 'MetadataStripper not available'}), 503
        
        result = metadata_stripper.inspect_metadata(tmp_path)

        # Ensure temp file is removed
        secure_delete_file(tmp_path)

        return jsonify({
            'success': True,
            'metadata': result
        })
        
    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            secure_delete_file(tmp_path)
        return jsonify({'success': False, 'error': str(e)}), 500



if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Starting OPSEC Toolkit Web Server")
    logger.info("=" * 60)
    # Read common host/port/debug settings
    debug_env = os.environ.get('FLASK_DEBUG', os.environ.get('DEBUG', 'false')).lower()
    debug_mode = debug_env in ('1', 'true', 'yes')
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', '5000'))

    if HAVE_FLASK and app is not None:
        try:
            app.run(host=host, port=port, debug=debug_mode, use_reloader=False, threaded=True)
        except Exception as e:
            logger.error(f"Failed to start Flask server: {e}")
            raise
    else:
        # Fallback simple static server when Flask is not installed
        from http.server import HTTPServer, SimpleHTTPRequestHandler

        class _Handler(SimpleHTTPRequestHandler):
            def do_GET(self):
                # Serve the SPA index from templates/index.html for root
                if self.path in ('', '/', '/index.html'):
                    try:
                        with open('templates/index.html', 'rb') as f:
                            content = f.read()
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.send_header('Content-Length', str(len(content)))
                        self.end_headers()
                        self.wfile.write(content)
                        return
                    except Exception as e:
                        self.send_error(404, 'Not Found')
                        return
                return SimpleHTTPRequestHandler.do_GET(self)

        try:
            server = HTTPServer((host, port), _Handler)
            logger.info(f"Started simple static server on http://{host}:{port}")
            server.serve_forever()
        except Exception as e:
            logger.error(f"Failed to start fallback static server: {e}")
            raise

