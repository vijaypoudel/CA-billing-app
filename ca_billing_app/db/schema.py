import sqlite3
import os

# Database schema and constants.
# Paths are now centrally managed in config_manager.py

def create_schema(connection):
    cursor = connection.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. FIRM OFFICE MASTER
    # Stores details for multiple CA offices if needed, though usually one firm.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS offices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        firm_name TEXT NOT NULL DEFAULT 'ANKITA AGARWAL & ASSOCIATES',
        address TEXT NOT NULL,
        gstin TEXT NOT NULL,
        pan TEXT NOT NULL,
        email TEXT,
        is_active BOOLEAN DEFAULT 1
    );
    """)

    # 2. CLIENT MASTER
    # GSTIN is unique. Client identity is strictly tied to GSTIN.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        gstin TEXT PRIMARY KEY,
        client_name TEXT NOT NULL,
        address TEXT,
        email TEXT,
        phone TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. BRANCH MASTER
    # Branches cannot be edited after creation.
    # Identity = Branch Name + City (enforced via unique index if needed, or app logic).
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS branches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        branch_name TEXT NOT NULL,
        city TEXT NOT NULL,
        bank_name TEXT NOT NULL,
        ifsc_code TEXT NOT NULL,
        account_number TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(bank_name, branch_name)
    );
    """)

    # 4. INVOICES
    # invoice_number format: A4CA/2526/MM/NNNN
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT NOT NULL UNIQUE,
        invoice_date DATE NOT NULL,
        financial_year TEXT NOT NULL, -- e.g., '25-26'
        month_str TEXT NOT NULL, -- e.g., '04'
        serial_number INTEGER NOT NULL, -- Resets monthly
        
        client_gstin TEXT NOT NULL,
        office_id INTEGER NOT NULL,
        
        -- Tax Applicability at Invoice Level
        -- 0=None, 1=IGST, 2=CGST+SGST
        tax_type TEXT CHECK(tax_type IN ('IGST', 'CGST_SGST', 'NONE')) NOT NULL,
        
        taxable_value REAL DEFAULT 0.0,
        cgst_amount REAL DEFAULT 0.0,
        sgst_amount REAL DEFAULT 0.0,
        igst_amount REAL DEFAULT 0.0,
        grand_total REAL DEFAULT 0.0,
        
        status TEXT DEFAULT 'Generated', -- Generated, Paid, Partially Paid, Cancelled
        pdf_path TEXT,

        allotted_bank TEXT,
        allotted_branch TEXT,
        allotted_city TEXT,

        place_of_supply TEXT,
        
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (client_gstin) REFERENCES clients(gstin),
        FOREIGN KEY (office_id) REFERENCES offices(id)
    );
    """)

    # 5. INVOICE ITEMS (Max 5 items enforced by app logic)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        hsn_code TEXT,
        amount REAL NOT NULL,
        gst_rate INTEGER NOT NULL, -- 0, 5, 12, 18
        
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
    );
    """)

    # 6. PAYMENTS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        amount_received REAL NOT NULL,
        payment_date DATE NOT NULL,
        payment_mode TEXT, -- NEFT, IMPS, CHEQUE, CASH
        reference_number TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
    );
    """)

    connection.commit()
