import sys
import os

# Add project root to sys.path to allow imports from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.legacy.login import LoginSystem

def run():
    """Entry point for the application."""
    try:
        app = LoginSystem()
        app.run()
    except KeyboardInterrupt:
        print("\n\n¡Adiós!")
        sys.exit(0)
    except Exception as e:
        print(f"Error crítico al iniciar la aplicación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()
