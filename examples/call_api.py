"""
Example script showing how to call the protected identity API endpoints.

Usage:
  - Set API_TOKEN in environment or the script will prompt for it
  - Optionally set API_BASE (default http://localhost:5000)

This script demonstrates listing identities, creating one, and burning it.
"""

import os
import sys
import uuid
import getpass

try:
    import requests
except Exception:
    print("The 'requests' library is required. Install with: pip install requests")
    sys.exit(1)

API_BASE = os.environ.get('API_BASE', 'http://localhost:5000')
API_TOKEN = os.environ.get('API_TOKEN')

if not API_TOKEN:
    API_TOKEN = getpass.getpass(prompt='Enter API token: ')

HEADERS = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Accept': 'application/json'
}


def list_identities():
    resp = requests.get(f"{API_BASE}/api/identities", headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    print('Identities:', data.get('identities'))


def create_identity(name):
    payload = {
        'name': name,
        'purpose': 'example from script',
        'generate_password': True,
        'generate_passphrase': False
    }
    resp = requests.post(f"{API_BASE}/api/identity/create", json=payload, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    print('Created identity:', data.get('identity'))
    return data.get('identity')


def burn_identity(name):
    resp = requests.delete(f"{API_BASE}/api/identity/{name}", headers=HEADERS)
    if resp.status_code == 200:
        print(f"Burned identity {name}")
    else:
        print('Failed to burn identity:', resp.status_code, resp.text)


if __name__ == '__main__':
    try:
        print('Listing identities...')
        list_identities()

        new_name = f"example-{uuid.uuid4().hex[:8]}"
        print(f'Creating identity: {new_name}')
        create_identity(new_name)

        print('Listing identities after creation...')
        list_identities()

        print(f'Burning identity: {new_name}')
        burn_identity(new_name)

        print('Listing identities after burn...')
        list_identities()

    except requests.HTTPError as e:
        print('HTTP error:', e.response.status_code, e.response.text)
    except Exception as e:
        print('Error:', str(e))
