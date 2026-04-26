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

    def generate_invoice_number(self, date_obj, office_id=None):
        """
        Format based on office configuration (Default: A4CA/FY/MM/NNNN).
        Resets every month. Uses initial_serial if this is the first invoice of the period.
        """
        fy = self.get_financial_year(date_obj)
        month_str = date_obj.strftime("%m")
        
        invoice_format = "A4CA/{FY}/{MM}/{SEQ}"
        initial_serial = 0
        
        conn = self.db.get_connection()
        try:
            if office_id:
                office_row = conn.execute("SELECT invoice_format, initial_serial FROM offices WHERE id = ?", (office_id,)).fetchone()
                if office_row:
                    r = dict(office_row)
                    invoice_format = r.get('invoice_format') or invoice_format
                    initial_serial = r.get('initial_serial') or initial_serial

            # Get ALL invoice numbers for this FY and month
            query = """
                SELECT invoice_number 
                FROM invoices 
                WHERE financial_year = ? AND month_str = ? AND office_id = ?
            """
            cursor = conn.execute(query, (fy, month_str, office_id)) if office_id else conn.execute("SELECT invoice_number FROM invoices WHERE financial_year = ? AND month_str = ?", (fy, month_str))
            rows = cursor.fetchall()
            
            max_serial = initial_serial - 1 if initial_serial > 0 else 0
            
            # Identify max serial from DB
            for row in rows:
                inv_num = row['invoice_number']
                # Best effort to extract serial number from the end of the string
                try:
                    # Look for {SEQ} location in format, but string formats vary. 
                    # Easiest heuristic: extract numbers from the end
                    import re
                    match = re.search(r'(\d+)$', inv_num)
                    if match:
                        serial = int(match.group(1))
                        if serial > max_serial:
                            max_serial = serial
                except Exception:
                    continue
            
            next_serial = max_serial + 1
            serial_str = f"{next_serial:03d}"
            
            # Apply format replacement
            formatted_num = invoice_format.replace('{FY}', fy).replace('{MM}', month_str).replace('{SEQ}', serial_str)
            
            return formatted_num, next_serial
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
            # Best effort parse for continuity
            import re
            match = re.search(r'(\d+)$', invoice_number)
            if match:
                serial_number = int(match.group(1))
            else:
                serial_number = 9999 # Fallback
        else:
            invoice_number, serial_number = self.generate_invoice_number(invoice_date, office_id=office_id)

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
