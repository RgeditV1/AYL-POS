import os
import sys


def is_frozen_app():
    return bool(getattr(sys, "frozen", False) or getattr(sys, "__compiled__", False))


def get_resource_root():
    # En Nuitka, os.path.abspath(__file__) apunta al interior del bundle extraído.
    # src/utils/resources.py -> src -> proyecto_root
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_resource_path(*parts):
    return os.path.join(get_resource_root(), *parts)
