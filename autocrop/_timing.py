import time

IMPORT_START = time.perf_counter()
_IMPORT_SECONDS = None


def mark_imports_complete():
    """Record package import duration once the public package is loaded."""
    global _IMPORT_SECONDS
    _IMPORT_SECONDS = time.perf_counter() - IMPORT_START


def import_seconds():
    """Return completed import duration, or duration so far while importing."""
    if _IMPORT_SECONDS is None:
        return time.perf_counter() - IMPORT_START
    return _IMPORT_SECONDS
