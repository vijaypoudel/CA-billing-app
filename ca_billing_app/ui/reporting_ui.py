from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QMessageBox, 
                               QFileDialog, QCheckBox, QDialog, QDialogButtonBox, QLabel,
                               QScrollArea, QHBoxLayout, QComboBox, QLineEdit, QTabWidget,
                               QTableWidget, QTableWidgetItem, QGroupBox, QFrame)
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import Qt
from services.reporting_service import ReportingService
from exports.excel_exporter import ExcelExporter
import datetime

class FieldSelectionDialog(QDialog):
    def __init__(self, available_fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Fields to Export")
        self.layout = QVBoxLayout(self)
        
        self.checkboxes = []
        for field in available_fields:
            cb = QCheckBox(field)
            cb.setChecked(True)
            self.layout.addWidget(cb)
            self.checkboxes.append(cb)
            
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
        
    def get_selected_fields(self):
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]

class ReportingUI(QWidget):
    def __init__(self):
        super().__init__()
        self.service = ReportingService()
        self.exporter = ExcelExporter()
        self.layout = QVBoxLayout(self)
        self.init_ui()
        
    def init_ui(self):
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #D5DBDB; background: white; }
            QTabBar::tab { 
                background: #F2F4F4; 
                padding: 10px 20px; 
                border: 1px solid #D5DBDB; 
                border-bottom: none; 
                margin-right: 2px;
                font-size: 13px;
                font-weight: bold;
                color: #566573;
            }
            QTabBar::tab:selected { 
                background: white; 
                border-top: 3px solid #3498DB;
                color: #2C3E50;
            }
        """)
        self.layout.addWidget(self.tabs)
        
        # --- Global Styles for this component ---
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', Arial; }
            QLabel { 
                color: #566573; 
                font-weight: bold; 
                background: transparent; 
                border: none;
                margin-right: 5px;
            }
            QComboBox, QLineEdit {
                padding: 6px 10px;
                border: 1px solid #D5DBDB;
                border-radius: 4px;
                background: white;
                min-width: 120px;
                min-height: 25px;
                max-height: 35px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: #AED6F1;
                border: 1px solid #D5DBDB;
            }
            QGroupBox {
                font-weight: bold; 
                color: #2C3E50; 
                border: 1px solid #EBEDEF; 
                border-radius: 8px;
                background-color: #FBFCFC;
                margin-top: 15px; 
                padding-top: 25px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
        """)

        self.primary_btn_style = """
            QPushButton {
                background-color: #3498DB; color: white; border-radius: 4px; padding: 8px 18px; font-weight: bold; min-height: 20px;
            }
            QPushButton:hover { background-color: #2980B9; }
        """
        self.success_btn_style = """
            QPushButton {
                background-color: #27AE60; color: white; border-radius: 4px; padding: 8px 18px; font-weight: bold; min-height: 20px;
            }
            QPushButton:hover { background-color: #229954; }
            QPushButton:disabled { background-color: #BDC3C7; color: #7F8C8D; }
        """
        
        # --- TAB 1: Invoice Report ---
        self.tabs.addTab(self.create_invoice_tab(), "Invoice Report")
        
        # --- TAB 2: Pending Payments ---
        self.tabs.addTab(self.create_pending_tab(), "Pending Payments")

        # --- TAB 3: Payment Received ---
        self.tabs.addTab(self.create_received_tab(), "Payment Received")

    def create_invoice_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Invoice Generation Summary")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2C3E50; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Filter Group
        filter_group = QGroupBox("Report Parameters")
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setContentsMargins(15, 20, 15, 15)
        filter_layout.setSpacing(20)
        
        self.inv_year_filter = QComboBox()
        self.populate_fy_dropdown(self.inv_year_filter)
        
        self.inv_month_filter = QComboBox()
        self.inv_month_filter.addItem("All Months", None)
        for i in range(1, 13):
            self.inv_month_filter.addItem(f"{i:02d}", f"{i:02d}")
            
        self.run_inv_btn = QPushButton("Run Analytics")
        self.run_inv_btn.clicked.connect(self.run_invoice_report)
        self.run_inv_btn.setStyleSheet(self.primary_btn_style)
        
        self.export_inv_btn = QPushButton("Export to Excel")
        self.export_inv_btn.clicked.connect(self.export_invoices_excel)
        self.export_inv_btn.setEnabled(False)
        self.export_inv_btn.setStyleSheet(self.success_btn_style)
        
        filter_layout.addWidget(QLabel("Financial Year:"))
        filter_layout.addWidget(self.inv_year_filter)
        filter_layout.addWidget(QLabel("Month:"))
        filter_layout.addWidget(self.inv_month_filter)
        filter_layout.addWidget(self.run_inv_btn)
        filter_layout.addWidget(self.export_inv_btn)
        filter_layout.addStretch()
        
        layout.addWidget(filter_group)
        
        # Table Area
        self.inv_table = QTableWidget()
        self.inv_table.setAlternatingRowColors(True)
        self.inv_table.setStyleSheet("QTableWidget { border: 1px solid #D5DBDB; selection-background-color: #AED6F1; }")
        layout.addWidget(self.inv_table)
        
        return tab

    def create_pending_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("Outstanding Receivables")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #C0392B; margin-bottom: 5px;")
        layout.addWidget(title)
        
        filter_group = QGroupBox("Filter Criteria")
        grid_vbox = QVBoxLayout(filter_group)
        grid_vbox.setContentsMargins(15, 20, 15, 15)
        grid_vbox.setSpacing(15)
        
        row1 = QHBoxLayout()
        self.pend_year_filter = QComboBox()
        self.populate_fy_dropdown(self.pend_year_filter)
        
        self.pend_month_filter = QComboBox()
        self.pend_month_filter.addItem("All Months", None)
        for i in range(1, 13):
            self.pend_month_filter.addItem(f"{i:02d}", f"{i:02d}")
            
        self.bank_filter = QLineEdit()
        self.bank_filter.setPlaceholderText("Filter by Bank...")
        
        self.branch_filter = QLineEdit()
        self.branch_filter.setPlaceholderText("Filter by Branch...")
        
        row1.addWidget(QLabel("FY:"))
        row1.addWidget(self.pend_year_filter)
        row1.addWidget(QLabel("Month:"))
        row1.addWidget(self.pend_month_filter)
        row1.addWidget(QLabel("Bank:"))
        row1.addWidget(self.bank_filter)
        row1.addWidget(QLabel("Branch:"))
        row1.addWidget(self.branch_filter)
        
        row2 = QHBoxLayout()
        self.run_pend_btn = QPushButton("View Pending Payments")
        self.run_pend_btn.clicked.connect(self.run_pending_report)
        self.run_pend_btn.setStyleSheet(self.primary_btn_style)
         
        self.export_pend_btn = QPushButton("Download Report (XLSX)")
        self.export_pend_btn.clicked.connect(self.export_pending_excel)
        self.export_pend_btn.setEnabled(False)
        self.export_pend_btn.setStyleSheet(self.success_btn_style)
        
        row2.addWidget(self.run_pend_btn)
        row2.addWidget(self.export_pend_btn)
        row2.addStretch()
        
        grid_vbox.addLayout(row1)
        grid_vbox.addLayout(row2)
        layout.addWidget(filter_group)
        
        self.pend_table = QTableWidget()
        self.pend_table.setAlternatingRowColors(True)
        layout.addWidget(self.pend_table)
        
        return tab

    def create_received_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("Payment Received Ledger")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #27AE60; margin-bottom: 5px;")
        layout.addWidget(title)
        
        filter_group = QGroupBox("Invoice History Search")
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setContentsMargins(15, 20, 15, 15)
        filter_layout.setSpacing(20)
        
        self.recv_year_filter = QComboBox()
        self.populate_fy_dropdown(self.recv_year_filter)
        
        self.recv_month_filter = QComboBox()
        self.recv_month_filter.addItem("All Months", None)
        for i in range(1, 13):
            self.recv_month_filter.addItem(f"{i:02d}", f"{i:02d}")
            
        self.run_recv_btn = QPushButton("Refresh Data")
        self.run_recv_btn.clicked.connect(self.run_received_report)
        self.run_recv_btn.setStyleSheet(self.primary_btn_style)
        
        self.export_recv_btn = QPushButton("Export Selection")
        self.export_recv_btn.clicked.connect(self.export_received_excel)
        self.export_recv_btn.setEnabled(False)
        self.export_recv_btn.setStyleSheet(self.success_btn_style)
        
        filter_layout.addWidget(QLabel("Invoice FY:"))
        filter_layout.addWidget(self.recv_year_filter)
        filter_layout.addWidget(QLabel("Month:"))
        filter_layout.addWidget(self.recv_month_filter)
        filter_layout.addWidget(self.run_recv_btn)
        filter_layout.addWidget(self.export_recv_btn)
        filter_layout.addStretch()
        
        layout.addWidget(filter_group)
        
        self.recv_table = QTableWidget()
        self.recv_table.setAlternatingRowColors(True)
        layout.addWidget(self.recv_table)
        
        return tab

    def populate_fy_dropdown(self, combo):
        # Add last 3 FYs and current
        # Logic: Current Date -> Current FY. Add -1, -2.
        combo.addItem("All Years", None)
        today = datetime.date.today()
        current_year = today.year
        if today.month < 4:
            current_year -= 1 # We are in end of FY, start year is prev year
            
        # Add Current + Next (for advance?) + Prev 2
        start_years = range(current_year - 2, current_year + 2)
        for y in reversed(start_years):
            fy_str = f"{str(y)[-2:]}{str(y+1)[-2:]}"
            combo.addItem(f"FY {y}-{y+1} ({fy_str})", fy_str)

    def run_invoice_report(self):
        month = self.inv_month_filter.currentData()
        fy = self.inv_year_filter.currentData()
        
        filters = {}
        if month: filters['month'] = month
        if fy: filters['fy'] = fy
        
        # Fetch data
        self.inv_data = self.service.export_data(query_type="invoices", filters=filters, fields_to_export=[])
        
        if not self.inv_data:
             self.inv_table.setRowCount(0)
             self.export_inv_btn.setEnabled(False)
             QMessageBox.information(self, "Info", "No data found.")
             return
             
        self.populate_table(self.inv_table, self.inv_data)
        self.export_inv_btn.setEnabled(True)

    def run_pending_report(self):
        month = self.pend_month_filter.currentData()
        fy = self.pend_year_filter.currentData()
        bank = self.bank_filter.text().strip() or None
        branch = self.branch_filter.text().strip() or None
        
        self.pend_data = self.service.get_pending_payments(month=month, bank=bank, branch=branch, fy=fy)
        if not self.pend_data:
             self.pend_table.setRowCount(0)
             self.export_pend_btn.setEnabled(False)
             QMessageBox.information(self, "Info", "No pending payments found.")
             return
             
        self.populate_table(self.pend_table, self.pend_data)
        self.export_pend_btn.setEnabled(True)

    def run_received_report(self):
        month = self.recv_month_filter.currentData()
        fy = self.recv_year_filter.currentData()
        
        self.recv_data = self.service.get_received_payments(month=month, fy=fy)
        if not self.recv_data:
            self.recv_table.setRowCount(0)
            self.export_recv_btn.setEnabled(False)
            QMessageBox.information(self, "Info", "No payments received found for criteria.")
            return
            
        self.populate_table(self.recv_table, self.recv_data)
        self.export_recv_btn.setEnabled(True)

    def populate_table(self, table, data):
        if not data: return
        headers = list(data[0].keys())
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(data))
        
        for r, row_data in enumerate(data):
            for c, header in enumerate(headers):
                val = row_data.get(header, "")
                table.setItem(r, c, QTableWidgetItem(str(val)))

    def get_export_path(self, report_type, fy_str=None, month_str=None):
        import os
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        
        # Determine Folder Structure based on Filters
        final_fy = fy_str if fy_str else "All_Years"
        final_month = month_str if month_str else "All_Months"
        
        # Folder: Desktop/AnkitaCA/Generated Reports/{FY}/{Month}/{Type}/
        folder = os.path.join(desktop, "AnkitaCA", "Generated Reports", final_fy, final_month, report_type)
        if not os.path.exists(folder):
            os.makedirs(folder)
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_{timestamp}.xlsx"
        return os.path.join(folder, filename)

    def export_invoices_excel(self):
        if not hasattr(self, 'inv_data') or not self.inv_data: return
        
        try:
            # 1. Field Selection
            headers = list(self.inv_data[0].keys())
            dlg = FieldSelectionDialog(headers, self)
            if dlg.exec() != QDialog.Accepted:
                return
            
            selected_fields = dlg.get_selected_fields()
            if not selected_fields: return
            
            # Filter Data
            filtered_data = []
            for row in self.inv_data:
                 filtered_data.append({k: row[k] for k in selected_fields if k in row})

            # 2. Custom Filename (Save As)
            fy = self.inv_year_filter.currentData()
            month = self.inv_month_filter.currentData()
            default_path = self.get_export_path("Invoices", fy_str=fy, month_str=month)
            
            final_path, _ = QFileDialog.getSaveFileName(self, "Save Report", default_path, "Excel Files (*.xlsx)")
            if not final_path: return
            
            self.exporter.export_to_excel(filtered_data, selected_fields, final_path)
            QMessageBox.information(self, "Success", f"Exported to:\n{final_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def export_pending_excel(self):
        if not hasattr(self, 'pend_data') or not self.pend_data: return
        try:
            fy = self.pend_year_filter.currentData()
            month = self.pend_month_filter.currentData()
            
            default_path = self.get_export_path("Pending_Payments", fy_str=fy, month_str=month)
            final_path, _ = QFileDialog.getSaveFileName(self, "Save Report", default_path, "Excel Files (*.xlsx)")
            if not final_path: return
            
            headers = list(self.pend_data[0].keys())
            self.exporter.export_to_excel(self.pend_data, headers, final_path)
            QMessageBox.information(self, "Success", f"Exported to:\n{final_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            
    def export_received_excel(self):
        if not hasattr(self, 'recv_data') or not self.recv_data: return
        try:
            fy = self.recv_year_filter.currentData()
            month = self.recv_month_filter.currentData()
            
            default_path = self.get_export_path("Payment_Received", fy_str=fy, month_str=month)
            final_path, _ = QFileDialog.getSaveFileName(self, "Save Report", default_path, "Excel Files (*.xlsx)")
            if not final_path: return

            headers = list(self.recv_data[0].keys())
            self.exporter.export_to_excel(self.recv_data, headers, final_path)
            QMessageBox.information(self, "Success", f"Exported to:\n{final_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
