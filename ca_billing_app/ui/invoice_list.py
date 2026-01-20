from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QPushButton, QInputDialog, QMessageBox, QHBoxLayout,
                               QLineEdit, QLabel, QDialog, QDialogButtonBox, QFormLayout, QDateEdit, QComboBox, QDoubleSpinBox, QMenu)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QBrush
from db.database import db_manager
from services.payment_service import PaymentService
import datetime

class PaymentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Payment")
        self.layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(datetime.date.today())
        form_layout.addRow("Payment Date:", self.date_edit)
        
        # Amount
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        form_layout.addRow("Amount Received:", self.amount_input)
        
        # Mode
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["NEFT", "UPI", "CHEQUE", "CASH", "IMPS", "TDS", "OTHERS"])
        form_layout.addRow("Mode:", self.mode_combo)
        
        # Reference
        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("Transaction ID / Cheque No / Notes")
        form_layout.addRow("Reference/Notes:", self.ref_input)
        
        self.layout.addLayout(form_layout)
        
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.validate_and_accept)
        btns.rejected.connect(self.reject)
        self.layout.addWidget(btns)
        
        self.data = None
        
    def validate_and_accept(self):
        try:
            amt = float(self.amount_input.text())
            if amt <= 0:
                raise ValueError("Amount must be positive.")
                
            self.data = {
                'date': self.date_edit.date().toPython(),
                'amount': amt,
                'mode': self.mode_combo.currentText(),
                'reference': self.ref_input.text().strip()
            }
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid amount.")

class InvoiceList(QWidget):
    def __init__(self):
        super().__init__()
        self.db = db_manager
        self.payment_service = PaymentService()
        self.layout = QVBoxLayout(self)
        
        # Search Bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Description, Invoice #, or Client...")
        self.search_input.textChanged.connect(self.filter_invoices)
        search_layout.addWidget(self.search_input)
        
        self.refresh_btn = QPushButton("Refresh List")
        self.refresh_btn.clicked.connect(self.load_invoices)
        search_layout.addWidget(self.refresh_btn)
        
        self.layout.addLayout(search_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Invoice No", "Date", "Client", "Total", "Status", "Desc Items", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)
        
        self.all_rows = [] # Cache for client-side filtering
        self.load_invoices()
        
    def load_invoices(self):
        conn = self.db.get_connection()
        try:
            # Join with invoice_items to get descriptions for search
            # We group cat description to avoid duplicate rows
            query = """
                SELECT i.id, i.invoice_number, i.invoice_date, c.client_name, i.grand_total, i.status,
                       GROUP_CONCAT(it.description, ', ') as descriptions
                FROM invoices i
                JOIN clients c ON i.client_gstin = c.gstin
                LEFT JOIN invoice_items it ON i.id = it.invoice_id
                GROUP BY i.id
                ORDER BY i.created_at DESC
            """
            rows = conn.execute(query).fetchall()
            self.all_rows = [dict(row) for row in rows]
            self.filter_invoices()
                
        except Exception as e:
            print(e)
        finally:
            conn.close()

    def filter_invoices(self):
        text = self.search_input.text().lower().strip()
        filtered = []
        for row in self.all_rows:
            # Search logic
            search_corpus = f"{row['invoice_number']} {row['client_name']} {row['descriptions'] or ''}".lower()
            if not text or text in search_corpus:
                filtered.append(row)
        
        self.populate_table(filtered)

    def populate_table(self, rows):
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(row['id'])))
            self.table.setItem(i, 1, QTableWidgetItem(row['invoice_number']))
            self.table.setItem(i, 2, QTableWidgetItem(str(row['invoice_date'])))
            self.table.setItem(i, 3, QTableWidgetItem(row['client_name']))
            self.table.setItem(i, 4, QTableWidgetItem(f"{row['grand_total']:.2f}"))
            # Status with color coding
            status_item = QTableWidgetItem(row['status'])
            status_item.setTextAlignment(Qt.AlignCenter)
            status_val = row['status'].lower()
            if status_val == 'paid':
                status_item.setBackground(QBrush(QColor("#4CAF50"))) # Green
                status_item.setForeground(QBrush(QColor("white")))
            elif status_val == 'cancelled':
                status_item.setBackground(QBrush(QColor("#F44336"))) # Red
                status_item.setForeground(QBrush(QColor("white")))
            elif status_val == 'partially paid':
                status_item.setBackground(QBrush(QColor("#FF9800"))) # Orange
                status_item.setForeground(QBrush(QColor("white")))
            elif status_val == 'generated':
                status_item.setBackground(QBrush(QColor("#2196F3"))) # Blue
                status_item.setForeground(QBrush(QColor("white")))
            
            self.table.setItem(i, 5, status_item)
            self.table.setItem(i, 6, QTableWidgetItem(row['descriptions'] or ""))
            
            # Simplified Actions Button
            actions_btn = QPushButton("Actions ▼")
            actions_btn.setStyleSheet("""
                QPushButton {
                    background-color: #607D8B; 
                    color: white; 
                    border-radius: 3px;
                    font-weight: bold;
                }
                QPushButton::menu-indicator { image: none; }
            """)
            
            menu = QMenu(self)
            inv_id = row['id']
            is_paid = row['status'].lower() == 'paid'
            
            edit_act = menu.addAction("Edit Invoice")
            edit_act.setEnabled(not is_paid)  # Freeze if paid
            edit_act.triggered.connect(lambda _, rid=inv_id: self.edit_invoice(rid))
            
            status_act = menu.addAction("Change Status")
            status_act.setEnabled(not is_paid)  # Freeze if paid
            status_act.triggered.connect(lambda _, rid=inv_id: self.change_status(rid))
            
            pay_act = menu.addAction("Add Payment")
            pay_act.setEnabled(not is_paid)  # Freeze if paid - already fully paid
            pay_act.triggered.connect(lambda _, rid=inv_id: self.open_payment_dialog(rid))
            
            hist_act = menu.addAction("View History")
            hist_act.triggered.connect(lambda _, rid=inv_id: self.view_history(rid))
            
            actions_btn.setMenu(menu)
            self.table.setCellWidget(i, 7, actions_btn)

    def open_payment_dialog(self, invoice_id):
        dlg = PaymentDialog(self)
        if dlg.exec():
            data = dlg.data
            try:
                self.payment_service.add_payment(
                    invoice_id, 
                    data['amount'], 
                    data['date'], 
                    data['mode'], 
                    data['reference']
                )
                QMessageBox.information(self, "Success", "Payment recorded.")
                self.load_invoices()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def view_history(self, invoice_id):
        payments = self.payment_service.get_payments_for_invoice(invoice_id)
        
        dlg = QDialog(self)
        dlg.setWindowTitle("Transaction History")
        dlg.resize(600, 300)
        layout = QVBoxLayout(dlg)
        
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Date", "Amount", "Mode", "Reference"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        table.setRowCount(len(payments))
        for i, p in enumerate(payments):
            table.setItem(i, 0, QTableWidgetItem(str(p['payment_date'])))
            table.setItem(i, 1, QTableWidgetItem(str(p['amount_received'])))
            table.setItem(i, 2, QTableWidgetItem(p['payment_mode']))
            table.setItem(i, 3, QTableWidgetItem(p['reference_number']))
            
        layout.addWidget(table)
        
        btn = QDialogButtonBox(QDialogButtonBox.Ok)
        btn.accepted.connect(dlg.accept)
        layout.addWidget(btn)
        
        
        dlg.exec()
    
    def edit_invoice(self, invoice_id):
        """Open a modal dialog to edit the invoice"""
        from ui.invoice_form import InvoiceForm # Local import to avoid circular dependency
        
        # Fetch invoice number for the title
        conn = self.db.get_connection()
        inv = conn.execute("SELECT invoice_number FROM invoices WHERE id=?", (invoice_id,)).fetchone()
        inv_num = inv['invoice_number'] if inv else "Unknown"
        conn.close()
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"UPDATING INVOICE # {inv_num}")
        dialog.resize(1100, 800)
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        
        edit_form = InvoiceForm(is_update_mode=True)
        edit_form.load_invoice_for_edit(invoice_id)
        
        # When update is successful, close the dialog automatically
        edit_form.invoice_processed.connect(dialog.accept)
        
        layout.addWidget(edit_form)
        
        # Optional: Add a cancel button at the bottom of the dialog for clarity
        cancel_btn = QPushButton("Cancel / Close Without Saving")
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)
        
        if dialog.exec() == QDialog.Accepted:
            # Refresh list if changes were saved
            self.load_invoices()
    
    def change_status(self, invoice_id):
        """Allow manual status change"""
        conn = self.db.get_connection()
        try:
            # Get current status
            current = conn.execute("SELECT status, invoice_number FROM invoices WHERE id=?", (invoice_id,)).fetchone()
            if not current:
                return
            
            statuses = ["Generated", "Paid", "Partially Paid", "Cancelled"]
            status, ok = QInputDialog.getItem(
                self, 
                "Change Status", 
                f"Invoice: {current['invoice_number']}\n\nSelect new status:",
                statuses,
                statuses.index(current['status']) if current['status'] in statuses else 0,
                False
            )
            
            if ok and status:
                conn.execute("UPDATE invoices SET status=? WHERE id=?", (status, invoice_id))
                conn.commit()
                QMessageBox.information(self, "Success", f"Status changed to: {status}")
                self.load_invoices()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()

