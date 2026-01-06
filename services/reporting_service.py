from db.database import db_manager
import logging

class ReportingService:
    def __init__(self):
        self.db = db_manager

    def get_gst_summary(self, financial_year, month=None):
        """
        Returns aggregated GST data.
        """
        conn = self.db.get_connection()
        query = """
            SELECT 
                SUM(taxable_value) as total_taxable,
                SUM(cgst_amount) as total_cgst,
                SUM(sgst_amount) as total_sgst,
                SUM(igst_amount) as total_igst,
                SUM(grand_total) as total_revenue
            FROM invoices
            WHERE financial_year = ? AND status != 'Cancelled'
        """
        params = [financial_year]
        
        if month:
            query += " AND month_str = ?"
            params.append(month)
            
        try:
            row = conn.execute(query, params).fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

    def get_pending_payments(self, month=None, bank=None, branch=None, gstin=None, fy=None):
        """
        Returns list of invoices that are not fully paid.
        Filters: month (str 'MM'), bank (str partial match), gstin (str exact), fy (str '2526')
        """
        conn = self.db.get_connection()
        query = """
            SELECT 
                i.id, i.invoice_number, i.invoice_date, c.client_name, i.grand_total, i.status, 
                i.allotted_bank, i.allotted_branch, i.client_gstin,
                (SELECT SUM(p.amount_received) FROM payments p WHERE p.invoice_id = i.id) as total_received
            FROM invoices i
            JOIN clients c ON i.client_gstin = c.gstin
            WHERE i.status IN ('Generated', 'Partially Paid')
        """
        params = []
        
        if month:
            query += " AND i.month_str = ?"
            params.append(month)
            
        if fy:
            query += " AND i.financial_year = ?"
            params.append(fy)
        
        if bank:
            query += " AND i.allotted_bank LIKE ?"
            params.append(f"%{bank}%")
            
        if branch:
            query += " AND i.allotted_branch LIKE ?"
            params.append(f"%{branch}%")
            
        if gstin:
            query += " AND i.client_gstin = ?"
            params.append(gstin)
            
        query += " ORDER BY i.invoice_date ASC"
        
        try:
            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                d['balance_due'] = d['grand_total'] - (d['total_received'] or 0.0)
                results.append(d)
            return results
        finally:
            conn.close()
    
    def export_data(self, query_type, filters=None, fields_to_export=None):
        conn = self.db.get_connection()
        try:
            # Build query dynamically based on type
            if query_type == "invoices":
                base_query = """
                    SELECT i.*, c.client_name, c.address as client_address
                    FROM invoices i
                    JOIN clients c ON i.client_gstin = c.gstin
                    WHERE 1=1
                """
                params = []
                
                if filters:
                    if 'month' in filters and filters['month']:
                        base_query += " AND i.month_str = ?"
                        params.append(filters['month'])
                    if 'fy' in filters and filters['fy']:
                        base_query += " AND i.financial_year = ?"
                        params.append(filters['fy'])
                    if 'year' in filters and filters['year']:
                         # Calendar year check on invoice_date
                         base_query += " AND strftime('%Y', i.invoice_date) = ?"
                         params.append(str(filters['year']))
                
                base_query += " ORDER BY i.invoice_date DESC"
                
                rows = conn.execute(base_query, params).fetchall()
                result = [dict(row) for row in rows]
                
                # Filter fields if needed
                if fields_to_export:
                    filtered_result = []
                    for item in result:
                        filtered_result.append({k: item[k] for k in fields_to_export if k in item})
                    return filtered_result
                return result
            return []
        finally:
            conn.close()

    def get_received_payments(self, month=None, fy=None):
        conn = self.db.get_connection()
        try:
            # Report of payments RECEIVED in a period
            # We filter by payment_date mostly
            query = """
                SELECT p.payment_date, c.client_name, i.invoice_number, p.amount_received, 
                       p.payment_mode, p.reference_number, p.notes
                FROM payments p
                JOIN invoices i ON p.invoice_id = i.id
                JOIN clients c ON i.client_gstin = c.gstin
                WHERE 1=1
            """
            params = []
            
            # Report of payments RECEIVED for invoices of a specific period
            # Filter by INVOICE Month/FY as per user request
            
            if month:
                query += " AND i.month_str = ?"
                params.append(month)
                
            if fy:
                query += " AND i.financial_year = ?"
                params.append(fy)
            
            query += " ORDER BY p.payment_date DESC"
            
            return [dict(row) for row in conn.execute(query, params).fetchall()]
        finally:
            conn.close()
