from db.database import db_manager
import logging
import datetime

class PaymentService:
    def __init__(self):
        self.db = db_manager

    def add_payment(self, invoice_id, amount, payment_date, mode, reference, notes=""):
        conn = self.db.get_connection()
        try:
            conn.execute("BEGIN")
            
            # Insert payment
            conn.execute("""
                INSERT INTO payments (invoice_id, amount_received, payment_date, payment_mode, reference_number, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (invoice_id, amount, payment_date, mode, reference, notes))
            
            # Check totals
            paid_row = conn.execute("SELECT SUM(amount_received) as total_paid FROM payments WHERE invoice_id = ?", (invoice_id,)).fetchone()
            total_paid = paid_row['total_paid'] or 0.0
            
            inv_row = conn.execute("SELECT grand_total, status FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
            grand_total = inv_row['grand_total']
            current_status = inv_row['status']
            
            new_status = current_status
            if current_status != 'Cancelled':
                if total_paid >= grand_total:
                    new_status = 'Paid'
                elif total_paid > 0:
                    new_status = 'Partially Paid'
                else:
                    new_status = 'Generated'
            
            if new_status != current_status:
                conn.execute("UPDATE invoices SET status = ? WHERE id = ?", (new_status, invoice_id))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Error adding payment: {e}")
            raise e
        finally:
            conn.close()

    def get_payments_for_invoice(self, invoice_id):
        conn = self.db.get_connection()
        try:
            return [dict(row) for row in conn.execute("SELECT * FROM payments WHERE invoice_id = ?", (invoice_id,)).fetchall()]
        finally:
            conn.close()
