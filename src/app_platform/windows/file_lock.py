import portalocker

LOCK_SH = portalocker.LOCK_SH
LOCK_EX = portalocker.LOCK_EX
LOCK_UN = portalocker.LOCK_UN


def flock(file_obj, operation):
    if operation == LOCK_UN:
        portalocker.unlock(file_obj)
        return

    portalocker.lock(file_obj, operation)
