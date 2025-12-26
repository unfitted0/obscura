"""
Command-line interface for OPSEC Toolkit
"""

import click
from pathlib import Path
import json
from colorama import init, Fore, Style

from opsec_toolkit.metadata_stripper import MetadataStripper
from opsec_toolkit.compartmentalization import IdentityManager, CompartmentalizationHelper
from opsec_toolkit.password_generator import PasswordGenerator
from opsec_toolkit.credential_vault import CredentialVault

init(autoreset=True)


@click.group()
@click.version_option(version="1.1.0")
def cli():
    """OPSEC Toolkit - Operational Security Tools"""
    pass


# ============================================================
# Password Generation Commands
# ============================================================
@cli.group()
def password():
    """Password generation utilities"""
    pass


@password.command()
@click.option('--length', '-l', default=20, help='Password length (default: 20)')
@click.option('--no-uppercase', is_flag=True, help='Exclude uppercase letters')
@click.option('--no-lowercase', is_flag=True, help='Exclude lowercase letters')
@click.option('--no-numbers', is_flag=True, help='Exclude numbers')
@click.option('--no-symbols', is_flag=True, help='Exclude symbols')
@click.option('--count', '-c', default=1, help='Number of passwords to generate')
def generate(length, no_uppercase, no_lowercase, no_numbers, no_symbols, count):
    """Generate random password(s)"""
    gen = PasswordGenerator()
    
    for i in range(count):
        pwd = gen.generate_password(
            length=length,
            uppercase=not no_uppercase,
            lowercase=not no_lowercase,
            numbers=not no_numbers,
            symbols=not no_symbols
        )
        strength = gen.get_strength(pwd)
        
        if count > 1:
            click.echo(f"\n{Fore.CYAN}Password {i+1}:")
        click.echo(f"{Fore.GREEN}{pwd}")
        click.echo(f"{Fore.YELLOW}Strength: {strength['description']} ({strength['entropy_bits']} bits)")


@password.command()
@click.option('--words', '-w', default=5, help='Number of words (default: 5)')
@click.option('--separator', '-s', default='-', help='Word separator (default: -)')
@click.option('--capitalize', is_flag=True, help='Capitalize each word')
@click.option('--count', '-c', default=1, help='Number of passphrases to generate')
def passphrase(words, separator, capitalize, count):
    """Generate random passphrase(s)"""
    gen = PasswordGenerator()
    
    for i in range(count):
        phrase = gen.generate_passphrase(
            words=words,
            separator=separator,
            capitalize=capitalize
        )
        
        if count > 1:
            click.echo(f"\n{Fore.CYAN}Passphrase {i+1}:")
        click.echo(f"{Fore.GREEN}{phrase}")


@password.command()
@click.option('--length', '-l', default=6, help='PIN length (default: 6)')
@click.option('--count', '-c', default=1, help='Number of PINs to generate')
def pin(length, count):
    """Generate numeric PIN(s)"""
    gen = PasswordGenerator()
    
    for i in range(count):
        generated_pin = gen.generate_pin(length=length)
        if count > 1:
            click.echo(f"{Fore.CYAN}PIN {i+1}: {Fore.GREEN}{generated_pin}")
        else:
            click.echo(f"{Fore.GREEN}{generated_pin}")


@password.command()
@click.argument('password_text')
def strength(password_text):
    """Check password strength"""
    gen = PasswordGenerator()
    result = gen.get_strength(password_text)
    
    click.echo(f"{Fore.CYAN}Password Analysis:")
    click.echo(f"  Length: {result['password_length']}")
    click.echo(f"  Entropy: {result['entropy_bits']} bits")
    
    # Color code the rating
    rating_colors = {
        "very_weak": Fore.RED,
        "weak": Fore.RED,
        "reasonable": Fore.YELLOW,
        "strong": Fore.GREEN,
        "very_strong": Fore.GREEN
    }
    color = rating_colors.get(result['rating'], Fore.WHITE)
    click.echo(f"  Rating: {color}{result['description']}")


# ============================================================
# Credential Vault Commands
# ============================================================
@cli.group()
def vault():
    """Encrypted credential storage"""
    pass


@vault.command()
@click.password_option(confirmation_prompt=True, help='Master password for the vault')
def init(password):
    """Initialize a new credential vault"""
    v = CredentialVault()
    
    if v.is_initialized():
        click.echo(f"{Fore.YELLOW}Vault already initialized. Use 'vault unlock' to access it.")
        return
    
    success, message = v.initialize(password)
    if success:
        click.echo(f"{Fore.GREEN}✓ {message}")
    else:
        click.echo(f"{Fore.RED}✗ {message}")


@vault.command()
@click.option('--password', '-p', prompt=True, hide_input=True, help='Master password')
def unlock(password):
    """Unlock the vault (for current session)"""
    v = CredentialVault()
    success, message = v.unlock(password)
    
    if success:
        click.echo(f"{Fore.GREEN}✓ {message}")
    else:
        click.echo(f"{Fore.RED}✗ {message}")


@vault.command()
@click.argument('identity_name')
@click.option('--service', '-s', required=True, help='Service name (e.g., reddit, twitter)')
@click.option('--username', '-u', help='Username for the service')
@click.option('--password', '-p', prompt=True, hide_input=True, 
              confirmation_prompt=True, help='Password for the service')
@click.option('--email', '-e', help='Email used for the service')
@click.option('--notes', '-n', help='Additional notes')
@click.option('--master-password', prompt=True, hide_input=True, help='Vault master password')
def add(identity_name, service, username, password, email, notes, master_password):
    """Add a credential to the vault"""
    v = CredentialVault()
    
    success, message = v.unlock(master_password)
    if not success:
        click.echo(f"{Fore.RED}✗ {message}")
        return
    
    success, message = v.add_credential(
        identity_name=identity_name,
        service=service,
        username=username,
        password=password,
        email=email,
        notes=notes
    )
    
    if success:
        click.echo(f"{Fore.GREEN}✓ {message}")
    else:
        click.echo(f"{Fore.RED}✗ {message}")


@vault.command()
@click.argument('identity_name')
@click.option('--master-password', prompt=True, hide_input=True, help='Vault master password')
def show(identity_name, master_password):
    """Show credentials for an identity"""
    v = CredentialVault()
    
    success, message = v.unlock(master_password)
    if not success:
        click.echo(f"{Fore.RED}✗ {message}")
        return
    
    credentials, message = v.get_credentials(identity_name)
    
    if not credentials:
        click.echo(f"{Fore.YELLOW}No credentials found for '{identity_name}'.")
        return
    
    click.echo(f"{Fore.CYAN}Credentials for '{identity_name}':")
    for cred in credentials:
        click.echo(f"\n  {Fore.GREEN}Service: {cred['service']}")
        click.echo(f"  {Fore.WHITE}ID: {cred['id']}")
        if cred.get('username'):
            click.echo(f"  Username: {cred['username']}")
        if cred.get('email'):
            click.echo(f"  Email: {cred['email']}")
        if cred.get('password'):
            click.echo(f"  Password: {cred['password']}")
        if cred.get('notes'):
            click.echo(f"  Notes: {cred['notes']}")
        click.echo(f"  Created: {cred['created']}")


@vault.command()
@click.option('--master-password', prompt=True, hide_input=True, help='Vault master password')
def list(master_password):
    """List all credentials (summary)"""
    v = CredentialVault()
    
    success, message = v.unlock(master_password)
    if not success:
        click.echo(f"{Fore.RED}✗ {message}")
        return
    
    summary, message = v.list_all_credentials()
    
    if not summary:
        click.echo(f"{Fore.YELLOW}No credentials in vault.")
        return
    
    click.echo(f"{Fore.CYAN}Vault Contents:")
    for identity_name, credentials in summary.items():
        click.echo(f"\n  {Fore.GREEN}{identity_name}:")
        for cred in credentials:
            click.echo(f"    - {cred['service']}: {cred.get('username', 'N/A')}")


@vault.command()
@click.option('--master-password', prompt=True, hide_input=True, help='Vault master password')
def stats(master_password):
    """Show vault statistics"""
    v = CredentialVault()
    
    success, message = v.unlock(master_password)
    if not success:
        click.echo(f"{Fore.RED}✗ {message}")
        return
    
    stats_data, message = v.get_vault_stats()
    
    click.echo(f"{Fore.CYAN}Vault Statistics:")
    click.echo(f"  Created: {stats_data.get('created', 'Unknown')}")
    click.echo(f"  Version: {stats_data.get('version', 'Unknown')}")
    click.echo(f"  Total identities: {stats_data.get('total_identities', 0)}")
    click.echo(f"  Total credentials: {stats_data.get('total_credentials', 0)}")
    click.echo(f"  Unique services: {stats_data.get('unique_services', 0)}")
    if stats_data.get('services'):
        click.echo(f"  Services: {', '.join(stats_data['services'])}")


@vault.command()
@click.argument('output_path')
@click.option('--master-password', prompt=True, hide_input=True, help='Vault master password')
@click.option('--export-password', prompt=True, hide_input=True, 
              confirmation_prompt=True, help='Password for the export file')
def export(output_path, master_password, export_password):
    """Export vault to encrypted file"""
    v = CredentialVault()
    
    success, message = v.unlock(master_password)
    if not success:
        click.echo(f"{Fore.RED}✗ {message}")
        return
    
    success, message = v.export_vault(output_path, export_password)
    if success:
        click.echo(f"{Fore.GREEN}✓ {message}")
    else:
        click.echo(f"{Fore.RED}✗ {message}")


@vault.command(name='import')
@click.argument('import_path')
@click.option('--master-password', prompt=True, hide_input=True, help='Vault master password')
@click.option('--import-password', prompt=True, hide_input=True, help='Import file password')
@click.option('--merge', is_flag=True, help='Merge with existing vault')
def import_vault(import_path, master_password, import_password, merge):
    """Import vault from encrypted file"""
    v = CredentialVault()
    
    success, message = v.unlock(master_password)
    if not success:
        click.echo(f"{Fore.RED}✗ {message}")
        return
    
    success, message = v.import_vault(import_path, import_password, merge)
    if success:
        click.echo(f"{Fore.GREEN}✓ {message}")
    else:
        click.echo(f"{Fore.RED}✗ {message}")


@vault.command()
@click.option('--current-password', prompt=True, hide_input=True, help='Current master password')
@click.option('--new-password', prompt=True, hide_input=True, 
              confirmation_prompt=True, help='New master password')
def change_password(current_password, new_password):
    """Change vault master password"""
    v = CredentialVault()
    
    success, message = v.change_master_password(current_password, new_password)
    if success:
        click.echo(f"{Fore.GREEN}✓ {message}")
    else:
        click.echo(f"{Fore.RED}✗ {message}")


# ============================================================
# Metadata Stripping Commands
# ============================================================
@cli.group()
def metadata():
    """Metadata stripping operations"""
    pass


@metadata.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file path')
def strip(file_path, output):
    """Strip metadata from a file"""
    stripper = MetadataStripper()
    file_path = Path(file_path)
    
    ext = file_path.suffix.lower()
    
    if ext in stripper.supported_image_formats:
        success, message = stripper.strip_image_metadata(file_path, output)
    elif ext in stripper.supported_audio_formats:
        success, message = stripper.strip_audio_metadata(file_path, output)
    elif ext in stripper.supported_video_formats:
        success, message = stripper.strip_video_metadata(file_path, output)
    else:
        click.echo(f"{Fore.RED}Unsupported file type: {ext}")
        return
    
    if success:
        click.echo(f"{Fore.GREEN}✓ {message}")
    else:
        click.echo(f"{Fore.RED}✗ {message}")


@metadata.command()
@click.argument('file_path', type=click.Path(exists=True))
def inspect(file_path):
    """Inspect metadata in a file"""
    stripper = MetadataStripper()
    result = stripper.inspect_metadata(file_path)
    
    if "error" in result:
        click.echo(f"{Fore.RED}Error: {result['error']}")
        return
    
    click.echo(f"{Fore.CYAN}File: {result['file']}")
    click.echo(f"{Fore.CYAN}Size: {result['size']} bytes")
    click.echo(f"\n{Fore.YELLOW}Metadata:")
    
    if result['metadata']:
        for key, value in result['metadata'].items():
            click.echo(f"  {key}: {value}")
    else:
        click.echo(f"  {Fore.GREEN}No metadata found")


@metadata.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
@click.option('--recursive', '-r', is_flag=True, help='Process subdirectories')
def batch(directory, recursive):
    """Batch strip metadata from multiple files"""
    stripper = MetadataStripper()
    results = stripper.batch_strip(directory, recursive=recursive)
    
    if "error" in results:
        click.echo(f"{Fore.RED}Error: {results['error']}")
        return
    
    click.echo(f"{Fore.CYAN}Batch Processing Results:")
    click.echo(f"  Processed: {results['processed']}")
    click.echo(f"  {Fore.GREEN}Successful: {results['successful']}")
    click.echo(f"  {Fore.RED}Failed: {results['failed']}")
    
    if results['errors']:
        click.echo(f"\n{Fore.YELLOW}Errors:")
        for error in results['errors']:
            click.echo(f"  {error}")


# ============================================================
# Identity Management Commands
# ============================================================
@cli.group()
def identity():
    """Identity and compartmentalization management"""
    pass


@identity.command()
@click.argument('name')
@click.option('--purpose', '-p', help='Purpose/description of this identity')
@click.option('--auto-rotate/--no-auto-rotate', default=True, help='Auto-rotate identity')
@click.option('--generate-password/--no-password', default=True, help='Generate password')
@click.option('--password-length', default=20, help='Password length (default: 20)')
@click.option('--passphrase', is_flag=True, help='Also generate a passphrase')
@click.option('--passphrase-words', default=5, help='Number of words in passphrase')
def create(name, purpose, auto_rotate, generate_password, password_length, 
           passphrase, passphrase_words):
    """Create a new compartmentalized identity"""
    manager = IdentityManager()
    identity = manager.create_identity(
        name, 
        purpose or "", 
        auto_rotate,
        generate_password=generate_password,
        password_length=password_length,
        generate_passphrase=passphrase,
        passphrase_words=passphrase_words
    )
    
    click.echo(f"{Fore.GREEN}✓ Identity created: {name}")
    click.echo(f"  Alias: {identity['alias']}")
    click.echo(f"  Email prefix: {identity['email_prefix']}")
    
    if 'password' in identity:
        click.echo(f"  Password: {identity['password']}")
        strength = identity.get('password_strength', {})
        click.echo(f"  Password strength: {strength.get('description', 'Unknown')}")
    
    if 'passphrase' in identity:
        click.echo(f"  Passphrase: {identity['passphrase']}")


@identity.command()
@click.argument('name')
@click.option('--show-password', is_flag=True, help='Show the password')
def get(name):
    """Get identity information"""
    manager = IdentityManager()
    identity = manager.get_identity(name, increment_use=False)
    
    if not identity:
        click.echo(f"{Fore.RED}Identity not found: {name}")
        return
    
    click.echo(f"{Fore.CYAN}Identity: {identity['name']}")
    click.echo(f"  Alias: {identity['alias']}")
    click.echo(f"  Email prefix: {identity['email_prefix']}")
    click.echo(f"  Purpose: {identity.get('purpose', 'N/A')}")
    click.echo(f"  Use count: {identity.get('use_count', 0)}")
    click.echo(f"  Created: {identity.get('created', 'Unknown')}")
    click.echo(f"  Last used: {identity.get('last_used', 'Never')}")
    
    if 'password' in identity:
        click.echo(f"  Password: {identity['password']}")
        strength = identity.get('password_strength', {})
        click.echo(f"  Password strength: {strength.get('description', 'Unknown')}")
    
    if 'passphrase' in identity:
        click.echo(f"  Passphrase: {identity['passphrase']}")


@identity.command()
@click.argument('name')
@click.option('--rotate-password/--keep-password', default=True, 
              help='Also rotate password')
def rotate(name, rotate_password):
    """Rotate an identity (generate new alias and password)"""
    manager = IdentityManager()
    identity = manager.rotate_identity(name, rotate_password=rotate_password)
    
    if not identity:
        click.echo(f"{Fore.RED}Identity not found: {name}")
        return
    
    click.echo(f"{Fore.GREEN}✓ Identity rotated: {name}")
    click.echo(f"  New alias: {identity['alias']}")
    click.echo(f"  New email prefix: {identity['email_prefix']}")
    
    if 'password' in identity and rotate_password:
        click.echo(f"  New password: {identity['password']}")


@identity.command()
@click.argument('name')
@click.option('--length', '-l', default=20, help='Password length')
def regenerate_password(name, length):
    """Regenerate only the password for an identity"""
    manager = IdentityManager()
    identity = manager.regenerate_password(name, password_length=length)
    
    if not identity:
        click.echo(f"{Fore.RED}Identity not found: {name}")
        return
    
    click.echo(f"{Fore.GREEN}✓ Password regenerated for: {name}")
    click.echo(f"  New password: {identity['password']}")
    strength = identity.get('password_strength', {})
    click.echo(f"  Strength: {strength.get('description', 'Unknown')}")


@identity.command()
@click.argument('name')
@click.confirmation_option(prompt='Are you sure you want to burn this identity?')
def burn(name):
    """Permanently delete (burn) an identity"""
    manager = IdentityManager()
    if manager.burn_identity(name):
        click.echo(f"{Fore.GREEN}✓ Identity burned: {name}")
    else:
        click.echo(f"{Fore.RED}Identity not found: {name}")


@identity.command(name='list')
def list_identities():
    """List all identities"""
    manager = IdentityManager()
    identities = manager.list_identities()
    
    if not identities:
        click.echo(f"{Fore.YELLOW}No identities found")
        return
    
    click.echo(f"{Fore.CYAN}Identities ({len(identities)}):")
    for name in identities:
        ident = manager.get_identity(name, increment_use=False)
        has_pwd = "🔑" if ident and 'password' in ident else ""
        click.echo(f"  {name}: {ident['alias']} (used {ident.get('use_count', 0)} times) {has_pwd}")


@identity.command()
def stats():
    """Show identity statistics"""
    manager = IdentityManager()
    stats_data = manager.get_identity_stats()
    
    click.echo(f"{Fore.CYAN}Identity Statistics:")
    click.echo(f"  Total identities: {stats_data.get('total', 0)}")
    click.echo(f"  Total uses: {stats_data.get('total_uses', 0)}")
    
    if stats_data.get('identities'):
        click.echo(f"\n{Fore.CYAN}Details:")
        for name, info in stats_data['identities'].items():
            pwd_status = "with password" if info.get('has_password') else "no password"
            click.echo(f"  {name}: {info.get('use_count', 0)} uses ({pwd_status})")


# Noise generation removed from CLI (optional separate tool)


# Digital hygiene CLI removed — functionality was removed from main app


# ============================================================
# Quick Generate Command (Convenience)
# ============================================================
@cli.command()
@click.option('--with-passphrase', is_flag=True, help='Also generate passphrase')
def quickgen(with_passphrase):
    """Quick generate a complete credentials set"""
    helper = CompartmentalizationHelper()
    creds = helper.generate_credentials_set(include_passphrase=with_passphrase)
    
    click.echo(f"{Fore.CYAN}Generated Credentials:")
    click.echo(f"  {Fore.GREEN}Username: {creds['username']}")
    click.echo(f"  {Fore.GREEN}Email prefix: {creds['email_prefix']}")
    click.echo(f"  {Fore.GREEN}Password: {creds['password']}")
    click.echo(f"  {Fore.YELLOW}Strength: {creds['password_strength']['description']}")
    
    if 'passphrase' in creds:
        click.echo(f"  {Fore.GREEN}Passphrase: {creds['passphrase']}")


# Main entry point
if __name__ == '__main__':
    cli()
