import os
import sys

def check():
    print(f"CWD: {os.getcwd()}")
    print(f"__file__: {__file__}")
    
    # Simulate DB path logic
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Assuming main.py logic (if this script is in same dir as main.py)
    data_dir = os.path.join(base_dir, 'data')
    db_file = os.path.join(data_dir, 'billing.db')
    
    print(f"Calculated DB Path: {db_file}")
    print(f"Exists? {os.path.exists(db_file)}")
    
    # Check the nested one
    nested = os.path.join(base_dir, 'ca_billing_app', 'data', 'billing.db')
    print(f"Nested DB Path: {nested}")
    print(f"Exists? {os.path.exists(nested)}")

if __name__ == "__main__":
    check()
