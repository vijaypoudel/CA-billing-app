from db.database import db_manager
import sqlite3

def seed_data():
    conn = db_manager.get_connection()
    try:
        # Offices (Usually auto-created, but ensuring)
        count = conn.execute("SELECT COUNT(*) as c FROM offices").fetchone()['c']
        if count == 0:
            conn.execute("""
                INSERT INTO offices (firm_name, address, gstin, pan) 
                VALUES ('ANKITA AGARWAL & ASSOCIATES', '123, CA Street, Delhi', '07AAAAA0000A1Z5', 'AAAAA0000A')
            """)
            
        # Clients
        clients = [
            ('07ABCDE1234F1Z5', 'Alpha Corp', 'Delhi, India', 'contact@alpha.com', '9876543210'),
            ('07XYZDE1234F1Z5', 'Beta Pvt Ltd', 'Noida, UP', 'billing@beta.com', '9123456780'),
            ('27ZZZZZ9999F1Z5', 'Gamma Industries', 'Mumbai, MH', 'accounts@gamma.com', '8888888888')
        ]
        
        for cli in clients:
            try:
                conn.execute("INSERT INTO clients (gstin, client_name, address, email, phone) VALUES (?, ?, ?, ?, ?)", cli)
            except sqlite3.IntegrityError:
                pass # Already exists

        # Branches
        branches = [
            ('HDFC Delhi', 'Delhi', 'HDFC Bank', 'CP Branch', 'HDFC0001234', '501000000000'),
            ('SBI Mumbai', 'Mumbai', 'SBI', 'Nariman Point', 'SBIN0004321', '10000000000')
        ]
        
        for br in branches:
            try:
                conn.execute("INSERT INTO branches (branch_name, city, bank_name, bank_branch, ifsc_code, account_number) VALUES (?, ?, ?, ?, ?, ?)", br)
            except sqlite3.IntegrityError:
                pass

        conn.commit()
        print("Seed data injected successfully.")
    except Exception as e:
        print(f"Error seeding data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_data()
