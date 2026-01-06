import sqlite3
import re
import os

DB_FILE = "ca_billing_app/data/billing.db"
GST_REGEX = r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
TEST_GSTIN = "27AFFPJ3635J1ZD"

def check_pos_column():
    print("--- Checking DB Schema ---")
    if not os.path.exists(DB_FILE):
        print("DB File not found.")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # Get columns for invoices
        cursor.execute("PRAGMA table_info(invoices)")
        cols = cursor.fetchall()
        col_names = [c[1] for c in cols]
        print("Columns in 'invoices':", col_names)
        
        if 'place_of_supply' in col_names:
            print("SUCCESS: 'place_of_supply' column exists.")
        else:
            print("FAILURE: 'place_of_supply' column MISSING.")
            
    except Exception as e:
        print(f"Error reading DB: {e}")
    finally:
        conn.close()

def test_gstin():
    print("\n--- Testing GSTIN Regex ---")
    print(f"Regex: {GST_REGEX}")
    print(f"Input: '{TEST_GSTIN}'")
    
    match = re.match(GST_REGEX, TEST_GSTIN)
    if match:
        print("Result: MATCH (Valid)")
    else:
        print("Result: NO MATCH (Invalid)")
        # Debug why
        # Check lengths
        print(f"Length: {len(TEST_GSTIN)}")
        for i, c in enumerate(TEST_GSTIN):
            print(f"Char {i}: {c} (ASCII {ord(c)})")

if __name__ == "__main__":
    check_pos_column()
    test_gstin()
