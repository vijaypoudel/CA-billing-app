import sqlite3
import os

import sys

# Ensure we can find the DB relative to THIS script
current_dir = os.path.dirname(os.path.abspath(__file__))
# Expected: .../ca_billing_app
project_root = os.path.dirname(current_dir)

# Check standard location
DB_FILE = os.path.join(project_root, "data", "billing.db")

# Check nested location (artifact of some copy or build?)
if not os.path.exists(DB_FILE):
    nested_db = os.path.join(project_root, "ca_billing_app", "data", "billing.db")
    if os.path.exists(nested_db):
        print(f"Found nested DB at: {nested_db}")
        DB_FILE = nested_db

def migrate_db():
    print(f"Looking for DB at: {DB_FILE}")
    if not os.path.exists(DB_FILE):
        print("DB File DOES NOT exist.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if columns exist
    try:
        cursor.execute("SELECT place_of_supply FROM invoices LIMIT 1")
    except sqlite3.OperationalError:
        print("Migrating: Adding place_of_supply to invoices table...")
        try:
            cursor.execute("ALTER TABLE invoices ADD COLUMN place_of_supply TEXT DEFAULT ''")
            conn.commit()
            print("Migration successful.")
        except Exception as e:
            print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
