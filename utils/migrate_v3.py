import sqlite3
import os
import sys

# Ensure we can find the DB relative to THIS script
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
DB_FILE = os.path.join(project_root, "data", "billing.db")

def migrate_db():
    print(f"Migrating DB at: {DB_FILE}")
    if not os.path.exists(DB_FILE):
        print("DB File DOES NOT exist.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Check if email column exists in offices
        cursor.execute("PRAGMA table_info(offices)")
        cols = [row[1] for row in cursor.fetchall()]
        
        if 'email' not in cols:
            print("Adding 'email' column to 'offices' table...")
            cursor.execute("ALTER TABLE offices ADD COLUMN email TEXT")
            print("Added successfully.")
        else:
            print("'email' column already exists in 'offices' table.")
            
        conn.commit()
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
