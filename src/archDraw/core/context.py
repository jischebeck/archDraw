import threading

# Thread-local stack to safely manage the `with` context
_context = threading.local()

def get_current_parent():
    """Returns the current container on top of the stack."""
    if not hasattr(_context, 'stack') or not _context.stack:
        return None
    return _context.stack[-1]