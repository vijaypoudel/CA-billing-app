import os
import json

CONFIG_DIR = os.path.join(os.path.expanduser("~"), "AnkitaCA")
CONFIG_FILE = os.path.join(CONFIG_DIR, "settings.json")

def get_default_db_path():
    return os.path.join(os.path.expanduser("~"), "Documents", "AnkitaCA", "data", "billing.db")

class ConfigManager:
    def __init__(self):
        self.ensure_config_dir()
        self.settings = self.load_settings()

    def ensure_config_dir(self):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)

    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default settings
        defaults = {
            "database_path": get_default_db_path(),
            "last_backup_date": None
        }
        self.save_settings(defaults)
        return defaults

    def save_settings(self, settings=None):
        if settings:
            self.settings = settings
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get_db_path(self):
        return self.settings.get("database_path", get_default_db_path())

    def set_db_path(self, path):
        self.settings["database_path"] = path
        self.save_settings()

# Global instance
config_manager = ConfigManager()
