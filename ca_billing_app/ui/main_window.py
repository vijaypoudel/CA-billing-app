from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget, 
                               QLabel, QMessageBox, QMenuBar)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from ui.invoice_form import InvoiceForm
from ui.invoice_list import InvoiceList
from ui.client_master import ClientMaster
from ui.branch_master import BranchMaster
from ui.office_master import OfficeMaster
from ui.reporting_ui import ReportingUI
from ui.help_ui import HelpUI

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CA Billing Application")
        self.setGeometry(100, 100, 1200, 800)
        self.setObjectName("MainWindow")  # For finding from InvoiceList
        self.init_ui()
        self._build_menu()

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
        self.tabs.addTab(HelpUI(), "Help & FAQ")
        
        self.tabs.currentChanged.connect(self.handle_tab_change)

    def _build_menu(self):
        menu_bar = self.menuBar()
        license_menu = menu_bar.addMenu("License")

        # Show current license status
        import license_manager
        _, expiry, msg = license_manager.check_license()
        status_action = QAction(f"Status: {msg}", self)
        status_action.setEnabled(False)
        license_menu.addAction(status_action)

        license_menu.addSeparator()

        # Update key action
        update_action = QAction("Update License Key…", self)
        update_action.triggered.connect(self._update_license)
        license_menu.addAction(update_action)

    def _update_license(self):
        from ui.license_ui import LicenseDialog
        dialog = LicenseDialog(message="Enter your new license key below.", parent=self)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowCloseButtonHint)
        dialog.exec()
    
    def handle_tab_change(self, index):
        """Auto-refresh specifically when landing on certain tabs"""
        tab_text = self.tabs.tabText(index)
        if tab_text == "Update Invoice":
            self.invoice_list.load_invoices()
        elif tab_text == "Create Invoice":
            self.invoice_form.load_clients() # Refresh client list in case new ones added
            self.invoice_form.load_offices()
            self.invoice_form.load_declaration_default()
    
    def edit_invoice_by_id(self, invoice_id):
        # We'll use a dialog for editing now, which will be initiated from InvoiceList
        pass
