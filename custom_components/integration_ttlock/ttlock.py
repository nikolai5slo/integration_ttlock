unlock_record_types = [1, 4, 7, 8, 9, 10, 12, 46, 49, 50, 55, 57, 58, 63]
lock_record_types = [11, 33, 34, 35, 36, 45, 47, 48, 61, 62]


def extract_lock_status_from_records_with_lock_id(lock_id, records):
    """Extracts latest lock status from records"""
    records = filter(lambda x: x["lockId"] == lock_id and x["success"] == 1, records)

    return extract_lock_status_from_records(records)


def extract_lock_status_from_records(records):
    """Extracts latest lock status from records"""
    records = sorted(records, key=lambda x: x["lockDate"], reverse=True)

    for rec in records:
        rec_type = rec["recordType"]
        if rec_type in unlock_record_types:
            return (1, rec["username"])
        if rec_type in lock_record_types:
            return (0, rec["username"])

    return (2, "")


def record_type_to_message(typ: str) -> str:
    """Convert record type to message"""
    if typ == 1:
        return "unlock by app"
    if typ == 4:
        return "unlock by passcode"
    if typ == 5:
        return "Rise the lock (for parking lock)"
    if typ == 6:
        return "Lower the lock (for parking lock)"
    if typ == 7:
        return "unlock by IC card"
    if typ == 8:
        return "unlock by fingerprint"
    if typ == 9:
        return "unlock by wrist strap"
    if typ == 10:
        return "unlock by Mechanical key"
    if typ == 11:
        return "lock by app"
    if typ == 12:
        return "unlock by gateway"
    if typ == 29:
        return "apply some force on the Lock"
    if typ == 30:
        return "Door sensor closed"
    if typ == 31:
        return "Door sensor open"
    if typ == 32:
        return "open from inside"
    if typ == 33:
        return "lock by fingerprint"
    if typ == 34:
        return "lock by passcode"
    if typ == 35:
        return "lock by IC card"
    if typ == 36:
        return "lock by Mechanical key"
    if typ == 37:
        return "Remote Control"
    if typ == 42:
        return "received new local mail"
    if typ == 43:
        return "received new other cities' mail"
    if typ == 44:
        return "Tamper alert"
    if typ == 45:
        return "Auto Lock"
    if typ == 46:
        return "unlock by unlock key"
    if typ == 47:
        return "lock by lock key"
    if typ == 48:
        return "System locked ( Caused by, for example: Using INVALID Passcode/Fingerprint/Card several times)"
    if typ == 49:
        return "unlock by hotel card"
    if typ == 50:
        return "Unlocked due to the high temperature"
    if typ == 52:
        return "Dead lock with APP"
    if typ == 53:
        return "Dead lock with passcode"
    if typ == 54:
        return "The car left (for parking lock)"
    if typ == 55:
        return "unlock with key fob"
    if typ == 57:
        return "Unlock with QR code success"
    if typ == 58:
        return "Unlock with QR code failed, it's expired"
    if typ == 59:
        return "Double locked"
    if typ == 60:
        return "Cancel double lock"
    if typ == 61:
        return "Lock with QR code success"
    if typ == 62:
        return "Lock with QR code failed, the lock is double locked"
    if typ == 63:
        return "Auto unlock at passage mode"
    return ""
