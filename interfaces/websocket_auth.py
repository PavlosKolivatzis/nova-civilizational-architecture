"""
WebSocket authentication utilities.
"""
import hmac
import hashlib
import time


def verify_token(token: str, secret: bytes, leeway_s: int = 60) -> bool:
    """
    Verify HMAC timestamp token.

    Args:
        token: Token in format "timestamp.hexdigest"
        secret: Shared secret key
        leeway_s: Time leeway in seconds

    Returns:
        bool: True if token is valid
    """
    try:
        # Split token into timestamp and MAC
        ts_str, mac_hex = token.split(".")
        ts = int(ts_str)

        # Check timestamp freshness
        if abs(time.time() - ts) > leeway_s:
            return False

        # Verify HMAC
        expected = hmac.new(secret, ts_str.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, mac_hex)
    except (ValueError, AttributeError):
        return False


def generate_token(secret: bytes) -> str:
    """
    Generate a new authentication token.

    Args:
        secret: Shared secret key

    Returns:
        str: New authentication token
    """
    ts_str = str(int(time.time()))
    mac = hmac.new(secret, ts_str.encode(), hashlib.sha256).hexdigest()
    return f"{ts_str}.{mac}"
