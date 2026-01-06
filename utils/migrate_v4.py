import sqlite3
import os

DB_PATH = "data/billing.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Starting migration: Fixing branch unique constraint...")
        
        # Check if the old constraint exists
        cursor.execute("PRAGMA table_info(branches)")
        columns = cursor.fetchall()
        
        # Create new table with correct constraint
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS branches_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch_name TEXT NOT NULL,
                city TEXT NOT NULL,
                bank_name TEXT NOT NULL,
                bank_branch TEXT NOT NULL,
                ifsc_code TEXT NOT NULL,
                account_number TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bank_name, branch_name)
            )
        """)
        
        # Copy data from old table
        cursor.execute("""
            INSERT INTO branches_new (id, branch_name, city, bank_name, bank_branch, ifsc_code, account_number, created_at)
            SELECT id, branch_name, city, bank_name, bank_branch, ifsc_code, account_number, created_at
            FROM branches
        """)
        
        # Drop old table and rename new one
        cursor.execute("DROP TABLE branches")
        cursor.execute("ALTER TABLE branches_new RENAME TO branches")
        
        conn.commit()
        print("Migration completed successfully!")
        print("Unique constraint changed from (branch_name, city) to (bank_name, branch_name)")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
