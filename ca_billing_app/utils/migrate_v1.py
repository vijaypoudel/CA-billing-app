import sqlite3
import os

DB_FOLDER = "ca_billing_app/data"
DB_FILE = os.path.join(DB_FOLDER, "billing.db")

def migrate_db():
    if not os.path.exists(DB_FILE):
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if columns exist
    try:
        cursor.execute("SELECT allotted_bank FROM invoices LIMIT 1")
    except sqlite3.OperationalError:
        print("Migrating: Adding allotted_bank, allotted_branch, allotted_city to invoices table...")
        try:
            cursor.execute("ALTER TABLE invoices ADD COLUMN allotted_bank TEXT DEFAULT ''")
            cursor.execute("ALTER TABLE invoices ADD COLUMN allotted_branch TEXT DEFAULT ''")
            cursor.execute("ALTER TABLE invoices ADD COLUMN allotted_city TEXT DEFAULT ''")
            conn.commit()
            print("Migration successful.")
        except Exception as e:
            print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
