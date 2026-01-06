import sqlite3
import os

DB_PATH = "data/billing.db"

def check():
    print(f"Checking {DB_PATH}...")
    if not os.path.exists(DB_PATH):
        print("File not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(invoices)")
        rows = cursor.fetchall()
        print(f"Columns in 'invoices':")
        found_pos = False
        for r in rows:
            print(f" - {r[1]}")
            if r[1] == 'place_of_supply':
                found_pos = True
        
        print(f"Has 'place_of_supply'? {found_pos}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check()
