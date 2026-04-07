import os
import msvcrt

LOCK_SH = 1
LOCK_EX = 2
LOCK_UN = 3


def _lock_length(file_obj):
    try:
        current = file_obj.tell()
        file_obj.seek(0, os.SEEK_END)
        size = file_obj.tell()
        file_obj.seek(current, os.SEEK_SET)
        return max(1, size)
    except Exception:
        return 1


def flock(file_obj, operation):
    length = _lock_length(file_obj)
    if operation == LOCK_UN:
        msvcrt.locking(file_obj.fileno(), msvcrt.LK_UNLCK, length)
    elif operation == LOCK_EX:
        msvcrt.locking(file_obj.fileno(), msvcrt.LK_LOCK, length)
    elif operation == LOCK_SH:
        msvcrt.locking(file_obj.fileno(), msvcrt.LK_RLCK, length)
    else:
        raise ValueError("Invalid lock operation")
