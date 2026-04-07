import os
import sys


def is_frozen_app():
    return bool(getattr(sys, "frozen", False))


def get_resource_root():
    if is_frozen_app():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_resource_path(*parts):
    return os.path.join(get_resource_root(), *parts)
