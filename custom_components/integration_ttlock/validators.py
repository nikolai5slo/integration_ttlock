def validate_lock_data(data):
    """Validates lock data"""

    return "lockId" in data and "lockName" in data
