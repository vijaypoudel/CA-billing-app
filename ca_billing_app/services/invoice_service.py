import datetime
from db.database import db_manager
import logging

class InvoiceService:
    def __init__(self):
        self.db = db_manager

    def get_financial_year(self, date_obj):
        """
        Returns FY string e.g., '2526' for April 2025 to March 2026.
        """
        year = date_obj.year
        month = date_obj.month
        
        if month >= 4:
            start_year = year
            end_year = year + 1
        else:
            start_year = year - 1
            end_year = year
            
        fy_str = f"{str(start_year)[-2:]}{str(end_year)[-2:]}"
        return fy_str

    def generate_invoice_number(self, date_obj):
        """
        Format: A4CA/FY/MM/NNNN
        Resets every month.
        Parses actual invoice numbers to handle custom invoice numbers correctly.
        """
        fy = self.get_financial_year(date_obj)
        month_str = date_obj.strftime("%m")
        
        conn = self.db.get_connection()
        try:
            # Get ALL invoice numbers for this FY and month
            query = """
                SELECT invoice_number 
                FROM invoices 
                WHERE financial_year = ? AND month_str = ?
            """
            cursor = conn.execute(query, (fy, month_str))
            rows = cursor.fetchall()
            
            # Parse invoice numbers to find the highest serial
            max_serial = 0
            for row in rows:
                inv_num = row['invoice_number']
                # Format: A4CA/2526/04/0001
                # Extract the last part (serial number)
                try:
                    parts = inv_num.split('/')
                    if len(parts) == 4:
                        serial = int(parts[3])
                        if serial > max_serial:
                            max_serial = serial
                except (ValueError, IndexError):
                    # Skip malformed invoice numbers
                    continue
            
            next_serial = max_serial + 1
            serial_str = f"{next_serial:04d}"
            return f"A4CA/{fy}/{month_str}/{serial_str}", next_serial
        finally:
            conn.close()

    def create_invoice(self, client_gstin, office_id, invoice_date, items, tax_type, allotted_details=None, manual_invoice_number=None):
        """
        allotted_details: dict with keys 'bank', 'branch', 'city'
        """
        if isinstance(invoice_date, str):
            invoice_date = datetime.datetime.strptime(invoice_date, "%Y-%m-%d").date()
            
        fy = self.get_financial_year(invoice_date)
        month_str = invoice_date.strftime("%m")
        
        bank = allotted_details.get('bank', '') if allotted_details else ''
        branch = allotted_details.get('branch', '') if allotted_details else ''
        city = allotted_details.get('city', '') if allotted_details else ''
        
        pos = allotted_details.get('pos', '') if allotted_details else ''
        
        if manual_invoice_number:
            invoice_number = manual_invoice_number
            # If manual, we still need a serial number for DB consistency, 
            # ideally we just grab the next one but don't use it in the string if overridden. 
            # But the requirement says "Manual override allowed".
            # To keep it simple and consistent, we'll assume the user provides the full string.
            # We will interpret the serial number from the manual string if it matches format
            # or just store 0/max if it breaks format to avoid collision. 
            # Best effort parse:
            parts = invoice_number.split('/')
            if len(parts) == 4 and parts[3].isdigit():
                serial_number = int(parts[3])
            else:
                serial_number = 9999 # Fallback
        else:
            invoice_number, serial_number = self.generate_invoice_number(invoice_date)

        # Calculate totals
        taxable_value = 0.0
        cgst_total = 0.0
        sgst_total = 0.0
        igst_total = 0.0
        
        for item in items:
            amt = float(item['amount'])
            rate = float(item['gst_rate']) # 0, 5, 12, 18
            
            taxable_value += amt
            
            if tax_type == 'IGST':
                igst_total += amt * (rate / 100.0)
            elif tax_type == 'CGST_SGST':
                cgst_total += amt * (rate / 2.0 / 100.0)
                sgst_total += amt * (rate / 2.0 / 100.0)
                
        grand_total = taxable_value + cgst_total + sgst_total + igst_total
        
        conn = self.db.get_connection()
        try:
            conn.execute("BEGIN")
            
            cursor = conn.execute("""
                INSERT INTO invoices (
                    invoice_number, invoice_date, financial_year, month_str, serial_number,
                    client_gstin, office_id, tax_type, 
                    taxable_value, cgst_amount, sgst_amount, igst_amount, grand_total, status,
                    allotted_bank, allotted_branch, allotted_city, place_of_supply
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Generated', ?, ?, ?, ?)
            """, (
                invoice_number, invoice_date, fy, month_str, serial_number,
                client_gstin, office_id, tax_type,
                taxable_value, cgst_total, sgst_total, igst_total, grand_total,
                bank, branch, city, pos
            ))
            
            invoice_id = cursor.lastrowid
            
            for item in items:
                conn.execute("""
                    INSERT INTO invoice_items (invoice_id, description, hsn_code, amount, gst_rate)
                    VALUES (?, ?, ?, ?, ?)
                """, (invoice_id, item['description'], item.get('hsn_code', ''), item['amount'], item['gst_rate']))
            
            conn.commit()
            return invoice_id, invoice_number
        except Exception as e:
            conn.rollback()
            logging.error(f"Error creating invoice: {e}")
            raise e
        finally:
            conn.close()

    def get_invoice_details(self, invoice_id):
        conn = self.db.get_connection()
        try:
            invoice = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
            if not invoice:
                return None
                
            items = conn.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,)).fetchall()
            client = conn.execute("SELECT * FROM clients WHERE gstin = ?", (invoice['client_gstin'],)).fetchone()
            office = conn.execute("SELECT * FROM offices WHERE id = ?", (invoice['office_id'],)).fetchone()
            
            return {
                "invoice": dict(invoice),
                "items": [dict(i) for i in items],
                "client": dict(client) if client else {},
                "office": dict(office) if office else {}
            }
        finally:
            conn.close()
