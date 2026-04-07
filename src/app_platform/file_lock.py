import platform


if platform.system() == "Windows":
    from src.app_platform.windows.file_lock import LOCK_EX, LOCK_SH, LOCK_UN, flock  # noqa: F401
else:
    from src.app_platform.linux.file_lock import LOCK_EX, LOCK_SH, LOCK_UN, flock  # noqa: F401
