"""
Singleton PeerStore instance for app-wide access.

Avoids circular import issues by providing module-independent storage.
"""

_instance = None


def init_peer_store(store):
    """
    Initialize the singleton PeerStore (called once at app startup).

    Args:
        store: PeerStore instance to register
    """
    global _instance
    _instance = store


def get_peer_store():
    """
    Get the singleton PeerStore instance.

    Returns:
        PeerStore instance if initialized, None otherwise
    """
    return _instance
