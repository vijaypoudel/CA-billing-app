import sqlite3
import os
import shutil
from .schema import create_schema
from config_manager import config_manager

class DatabaseManager:
    def __init__(self):
        self.db_path = config_manager.get_db_path()
        self.migrate_if_needed()
        self.ensure_db_exists()

    def migrate_if_needed(self):
        # Old local path
        old_dir = os.path.join(os.getcwd(), "data")
        old_file = os.path.join(old_dir, "billing.db")
        
        # If old data exists AND new location is empty, migrate it
        if os.path.exists(old_file) and not os.path.exists(self.db_path):
            new_dir = os.path.dirname(self.db_path)
            if not os.path.exists(new_dir):
                os.makedirs(new_dir)
            
            try:
                # Copy instead of move for safety during first transition
                shutil.copy2(old_file, self.db_path)
                print(f"Data migrated: {old_file} -> {self.db_path}")
                # Optional: rename old file to .old instead of deleting immediately
                os.rename(old_file, old_file + ".migrated")
            except Exception as e:
                print(f"Migration failed: {e}")

    def ensure_db_exists(self):
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Connect and initialize schema if new
        conn = sqlite3.connect(self.db_path)
        create_schema(conn)
        conn.close()

    def get_connection(self):
        """Returns a new connection object."""
        # Refresh path from config in case it changed in UI
        self.db_path = config_manager.get_db_path()
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn

# Global instance
db_manager = DatabaseManager()
