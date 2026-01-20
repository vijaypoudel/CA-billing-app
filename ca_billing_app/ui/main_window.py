from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget, 
                               QLabel, QMessageBox)
from PySide6.QtCore import Qt
from ui.invoice_form import InvoiceForm
from ui.invoice_list import InvoiceList
from ui.client_master import ClientMaster
from ui.branch_master import BranchMaster
from ui.office_master import OfficeMaster
from ui.reporting_ui import ReportingUI

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CA Billing Application")
        self.setGeometry(100, 100, 1200, 800)
        self.setObjectName("MainWindow")  # For finding from InvoiceList
        self.init_ui()

    def init_ui(self):
        # Global stylesheet for dropdown opaque backgrounds (Windows fix)
        self.setStyleSheet("""
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: #AED6F1;
                border: 1px solid #D5DBDB;
            }
        """)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.invoice_form = InvoiceForm()
        self.invoice_list = InvoiceList()
        
        self.tabs.addTab(OfficeMaster(), "Business Setup")
        self.tabs.addTab(ClientMaster(), "Client Setup")
        self.tabs.addTab(BranchMaster(), "Bank Setup")
        self.tabs.addTab(self.invoice_form, "Create Invoice")
        self.tabs.addTab(self.invoice_list, "Update Invoice")
        self.tabs.addTab(ReportingUI(), "Reports")
    
    def edit_invoice_by_id(self, invoice_id):
        # We'll use a dialog for editing now, which will be initiated from InvoiceList
        pass


