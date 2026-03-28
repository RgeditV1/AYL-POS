import json
import os
from src.core.config import SETTINGS_JSON

class SettingsManager:
    """Manages store settings and configuration."""

    def __init__(self, settings_file=None):
        self.settings_file = settings_file or SETTINGS_JSON
        self.default_settings = {
            "business_name": "Mi Tienda",
            "address": "Calle Principal 123",
            "phone": "555-0199",
            "cashier_name": "Cajero",
            "logo_path": ""
        }

    def load_settings(self):
        """Load settings from JSON file with default fallback."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    # Merge with defaults
                    settings = self.default_settings.copy()
                    settings.update(loaded)
                    return settings
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            
        return self.default_settings.copy()

    def save_settings(self, settings):
        """Save settings to JSON file."""
        try:
            # Ensure only relevant keys are saved
            clean_settings = {k: settings.get(k, "") for k in self.default_settings.keys()}
            
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(clean_settings, f, indent=4)
            return True, "Configuración guardada exitosamente."
        except Exception as e:
            return False, f"No se pudo guardar la configuración: {e}"
