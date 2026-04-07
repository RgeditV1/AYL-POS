import fcntl

LOCK_SH = fcntl.LOCK_SH
LOCK_EX = fcntl.LOCK_EX
LOCK_UN = fcntl.LOCK_UN


def flock(file_obj, operation):
    fcntl.flock(file_obj, operation)
