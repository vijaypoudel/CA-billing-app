"""
License Manager for CA Billing App.

Uses HMAC-SHA256 to create tamper-proof license keys that encode an expiry date.
Keys are stored in the user's config directory alongside settings.json.
"""

import os
import json
import hmac
import hashlib
import base64
from datetime import datetime, date

# -------------------------------------------------------------------
# SECRET – This is the shared secret baked into the app binary.
# It is NOT visible to end-users because PyInstaller bundles it inside
# the compiled executable.  Change this to any random string you like.
# -------------------------------------------------------------------
_SECRET = b"AnkitaCA-2026-BillingApp-LicenseKey-X9k3mP"

LICENSE_FILE = os.path.join(
    os.path.expanduser("~"), "AnkitaCA", "license.json"
)


def _sign(payload: str) -> str:
    """Create an HMAC signature for a payload string."""
    return hmac.new(_SECRET, payload.encode(), hashlib.sha256).hexdigest()


def generate_key(expiry_date: date) -> str:
    """
    Generate a license key that encodes the given expiry date.

    The key format is:   base64( expiry_iso | hmac_signature )
    Example output:      Q0EtMjAyNy0wMy0zMXw1YTJiM2M0ZDVlNmY3...

    This function is used by the DEVELOPER ONLY (via generate_license_key.py).
    """
    payload = expiry_date.isoformat()          # e.g. "2027-03-31"
    signature = _sign(payload)
    raw = f"{payload}|{signature}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def validate_key(key: str) -> tuple:
    """
    Validate a license key.

    Returns:
        (is_valid: bool, expiry_date: date | None, message: str)
    """
    try:
        raw = base64.urlsafe_b64decode(key.encode()).decode()
        parts = raw.split("|")
        if len(parts) != 2:
            return False, None, "Invalid key format."

        payload, provided_sig = parts
        expected_sig = _sign(payload)

        if not hmac.compare_digest(provided_sig, expected_sig):
            return False, None, "Invalid license key."

        expiry = date.fromisoformat(payload)
        if date.today() > expiry:
            return False, expiry, f"License expired on {expiry.strftime('%d %b %Y')}."

        return True, expiry, f"License valid until {expiry.strftime('%d %b %Y')}."

    except Exception:
        return False, None, "Invalid license key."


# ----- Persistence helpers -----

def _ensure_license_dir():
    d = os.path.dirname(LICENSE_FILE)
    if not os.path.exists(d):
        os.makedirs(d)


def save_license(key: str):
    """Save a license key to the local config file."""
    _ensure_license_dir()
    data = {"license_key": key, "saved_at": datetime.now().isoformat()}
    with open(LICENSE_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_license() -> str | None:
    """Load the saved license key, or return None if not found."""
    if os.path.exists(LICENSE_FILE):
        try:
            with open(LICENSE_FILE, "r") as f:
                data = json.load(f)
            return data.get("license_key")
        except Exception:
            pass
    return None


def check_license() -> tuple:
    """
    Main startup check.

    Returns:
        (is_licensed: bool, expiry_date: date | None, message: str)
    """
    key = load_license()
    if not key:
        return False, None, "No license key found. Please enter a valid license key."

    return validate_key(key)
