import platform


if platform.system() == "Windows":
    from src.platform.windows.file_lock import LOCK_EX, LOCK_SH, LOCK_UN, flock  # noqa: F401
else:
    from src.platform.linux.file_lock import LOCK_EX, LOCK_SH, LOCK_UN, flock  # noqa: F401
