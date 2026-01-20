from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                               QHeaderView, QMessageBox, QLabel, QComboBox, QDateEdit, 
                               QCompleter, QCheckBox, QTextEdit, QGroupBox, QFrame,
                               QScrollArea)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from db.database import db_manager
from services.invoice_service import InvoiceService
from pdf.invoice_pdf import InvoicePDFGenerator
import datetime

class InvoiceForm(QWidget):
    invoice_processed = Signal()
    
    def __init__(self, is_update_mode=False):
        super().__init__()
        self.invoice_service = InvoiceService()
        self.pdf_generator = InvoicePDFGenerator()
        self.db = db_manager
        self.is_update_mode = is_update_mode
        self.editing_invoice_id = None  # Track which invoice we're editing
        
        # Runtime Schema Check
        self.check_db_schema()
        
        # Create outer scroll area for entire form
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Content widget inside scroll area
        content_widget = QWidget()
        self.layout = QVBoxLayout(content_widget)
        self.layout.setSpacing(12)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Title based on mode
        self.title_label = QLabel("Update Invoice" if is_update_mode else "Create New Invoice")
        self.title_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: #2C3E50;
            padding-bottom: 5px; 
            border-bottom: 2px solid #3498DB;
            margin-bottom: 10px;
        """)
        self.layout.addWidget(self.title_label)

        # --- Top Section: Business & Client (GROUPED) ---
        top_hbox = QHBoxLayout()
        
        # 1. Business Info Group
        business_group = QGroupBox("1. Your Business Details")
        business_group.setStyleSheet("font-weight: bold; color: #34495E;")
        bus_layout = QVBoxLayout(business_group)
        
        self.office_combo = QComboBox()
        self.office_combo.setStyleSheet("font-weight: normal; padding: 5px;")
        self.office_combo.currentIndexChanged.connect(self.on_office_changed)
        
        self.office_display = QTextEdit()
        self.office_display.setReadOnly(True)
        self.office_display.setMaximumHeight(80)
        self.office_display.setMinimumWidth(200)
        self.office_display.setMaximumWidth(500)
        self.office_display.setStyleSheet("""
            background-color: #F8F9F9; 
            border: 1px solid #D5DBDB; 
            color: #566573;
            font-weight: normal;
        """)
        
        bus_layout.addWidget(QLabel("Select Office:"))
        self.office_combo.setMinimumWidth(200)
        self.office_combo.setMaximumWidth(500)
        bus_layout.addWidget(self.office_combo)
        bus_layout.addWidget(QLabel("Registered Address:"))
        bus_layout.addWidget(self.office_display)
        
        # 2. Invoice Details Group
        invoice_details_group = QGroupBox("2. Invoice & Client Details")
        invoice_details_group.setStyleSheet("font-weight: bold; color: #34495E;")
        inv_form = QFormLayout(invoice_details_group)
        inv_form.setSpacing(10)
        inv_form.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        
        # Client Selection (Searchable)
        self.client_combo = QComboBox()
        self.client_combo.setEditable(True)
        self.client_combo.setInsertPolicy(QComboBox.NoInsert)
        self.client_combo.completer().setCompletionMode(QCompleter.PopupCompletion)
        self.client_combo.completer().setFilterMode(Qt.MatchContains)
        self.client_combo.lineEdit().setPlaceholderText("Search Client (GSTIN / Name)...")
        self.client_combo.setStyleSheet("font-weight: normal; padding: 5px;")
        self.client_combo.setMinimumWidth(250)
        self.client_combo.setMaximumWidth(500)
        self.client_combo.currentIndexChanged.connect(self.auto_select_tax_type)
        
        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setStyleSheet("font-weight: normal; padding: 5px;")
        self.date_edit.setMinimumWidth(150)
        self.date_edit.setMaximumWidth(250)
        
        # POS
        from utils.gst_states import get_state_list
        self.pos_combo = QComboBox()
        self.pos_combo.setEditable(True)
        self.pos_combo.addItems(get_state_list())
        self.pos_combo.setCurrentIndex(-1)
        self.pos_combo.setStyleSheet("font-weight: normal; padding: 5px;")
        self.pos_combo.setMinimumWidth(200)
        self.pos_combo.setMaximumWidth(400)
        
        # Tax Type
        self.tax_combo = QComboBox()
        self.tax_combo.addItems(["IGST", "CGST_SGST", "NONE"])
        self.tax_combo.setStyleSheet("font-weight: normal; padding: 5px;")
        self.tax_combo.setMinimumWidth(150)
        self.tax_combo.setMaximumWidth(250)
        
        inv_form.addRow("Client (GSTIN):", self.client_combo)
        inv_form.addRow("Invoice Date:", self.date_edit)
        inv_form.addRow("Place of Supply:", self.pos_combo)
        inv_form.addRow("Tax Type:", self.tax_combo)
        
        top_hbox.addWidget(business_group, 4)
        top_hbox.addWidget(invoice_details_group, 6)
        self.layout.addLayout(top_hbox)

        # --- Middle Section: Bank Details & Sequence (STREMLINED) ---
        mid_layout = QHBoxLayout()
        
        # Bank Selector
        bank_group = QGroupBox("3. Allotted Bank (For Footer)")
        bank_group.setStyleSheet("font-weight: bold; color: #34495E;")
        bank_hbox = QHBoxLayout(bank_group)
        
        self.bank_combo = QComboBox()
        self.bank_combo.setPlaceholderText("Select Bank")
        self.bank_combo.currentTextChanged.connect(self.load_bank_cities)
        
        self.city_combo = QComboBox()
        self.city_combo.setPlaceholderText("Select City")
        self.city_combo.currentTextChanged.connect(self.load_bank_branches)
        
        self.branch_combo = QComboBox()
        self.branch_combo.setPlaceholderText("Select Branch")
        
        bank_hbox.addWidget(self.bank_combo)
        bank_hbox.addWidget(self.city_combo)
        bank_hbox.addWidget(self.branch_combo)
        mid_layout.addWidget(bank_group, 7)

        # Dummy Invoice logic (If Create Mode)
        if not is_update_mode:
            dummy_group = QGroupBox("Generate Dummy Invoice")
            dummy_group.setStyleSheet("font-weight: bold; color: #34495E;")
            dummy_vbox = QVBoxLayout(dummy_group)
            self.skip_number_btn = QPushButton("Generate Dummy/Placeholder")
            self.skip_number_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E67E22; 
                    color: white; 
                    padding: 8px; 
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #D35400; }
            """)
            self.skip_number_btn.clicked.connect(self.skip_invoice_number)
            dummy_vbox.addWidget(self.skip_number_btn)
            mid_layout.addWidget(dummy_group, 3)

        self.layout.addLayout(mid_layout)

        # --- Items Section ---
        items_group = QGroupBox("4. Items & Services")
        items_group.setStyleSheet("font-weight: bold; color: #34495E;")
        items_vbox = QVBoxLayout(items_group)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["Description", "HSN", "Amount", "GST Rate %"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setRowCount(1)
        self.items_table.setStyleSheet("font-weight: normal;")
        # Set minimum height to show all 5 rows without internal scroll
        self.items_table.setMinimumHeight(200)
        self.items_table.verticalHeader().setDefaultSectionSize(35)
        
        # Row Control Buttons
        row_btn_hbox = QHBoxLayout()
        self.add_row_btn = QPushButton("+ Add Item")
        self.add_row_btn.setStyleSheet("""
            QPushButton { background-color: #ECF0F1; color: #2C3E50; border: 1px solid #BDC3C7; padding: 5px 15px; border-radius: 3px; }
            QPushButton:hover { background-color: #D5DBDB; }
        """)
        self.add_row_btn.clicked.connect(self.add_item_row)
        
        self.remove_row_btn = QPushButton("- Remove")
        self.remove_row_btn.setStyleSheet("color: #7B241C; background: none; border: none; font-weight: normal; text-decoration: underline;")
        self.remove_row_btn.clicked.connect(self.remove_item_row)
        
        row_btn_hbox.addWidget(self.add_row_btn)
        row_btn_hbox.addWidget(self.remove_row_btn)
        row_btn_hbox.addStretch()
        
        items_vbox.addWidget(self.items_table)
        items_vbox.addLayout(row_btn_hbox)
        self.layout.addWidget(items_group)
        
        # --- Bottom Section: Totals & Generate ---
        bottom_hbox = QHBoxLayout()
        bottom_hbox.setSpacing(20)
        
        # Calculation display area
        calc_frame = QFrame()
        calc_frame.setStyleSheet("background-color: #EBF5FB; border-radius: 5px; padding: 10px; border: 1px solid #AED6F1;")
        calc_vbox = QVBoxLayout(calc_frame)
        
        # Calc button is now a secondary link/small button
        self.calc_btn = QPushButton("Calculate Row Totals (Optional)")
        self.calc_btn.setStyleSheet("color: #3498DB; background: none; border: none; text-decoration: underline; text-align: left; font-weight: normal;")
        self.calc_btn.clicked.connect(self.calculate_totals)
        
        self.totals_label = QLabel("Taxable: 0.00 | Tax: 0.00 | Grand Total: 0.00")
        self.totals_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #21618C;")
        
        calc_vbox.addWidget(self.calc_btn)
        calc_vbox.addWidget(self.totals_label)
        bottom_hbox.addWidget(calc_frame, 7)
        
        # FINAL CTA
        self.gen_btn = QPushButton("GENERATE INVOICE & PDF" if not is_update_mode else "UPDATE INVOICE & REGENERATE PDF")
        self.gen_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60; 
                color: white; 
                padding: 15px 30px; 
                font-weight: bold; 
                font-size: 16px; 
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        self.gen_btn.clicked.connect(self.generate_invoice)
        bottom_hbox.addWidget(self.gen_btn, 3)
        
        self.layout.addLayout(bottom_hbox)
        
        # Initial loads
        # (load_offices ensures self.office_display is set)
        self.load_banks()
        self.load_offices()
        self.load_clients()

    def check_db_schema(self):
        conn = self.db.get_connection()
        try:
            # Check for place_of_supply
            cursor = conn.execute("PRAGMA table_info(invoices)")
            cols = [row['name'] for row in cursor.fetchall()]
            if 'place_of_supply' not in cols:
                QMessageBox.critical(self, "Critical Error", 
                    f"Database Schema Mismatch!\n\n"
                    f"Connected to: {self.db.db_path}\n"
                    f"Column 'place_of_supply' is MISSING.\n\n"
                    "Please close this app and run 'python3 fix_db.py' again."
                )
        except Exception as e:
             print(f"Schema check failed: {e}")
        finally:
            conn.close()
        

        
    def showEvent(self, event):
        # Auto-refresh dropdowns when tab is switched to
        # ONLY if we are NOT currently editing an invoice (to prevent wiping out loaded data)
        if not self.editing_invoice_id:
            self.load_offices()
            self.load_clients()
            self.load_banks()
        super().showEvent(event)
        
    def load_offices(self):
        self.office_combo.blockSignals(True)
        self.office_combo.clear()
        conn = self.db.get_connection()
        try:
            # Check if offices exist, if not create default
            count = conn.execute("SELECT COUNT(*) as c FROM offices").fetchone()['c']
            if count == 0:
                conn.execute("""
                    INSERT INTO offices (firm_name, address, gstin, pan) 
                    VALUES ('ANKITA AGARWAL & ASSOCIATES', 'Registered Office Address', 'DEFAULT_GSTIN', 'DEFAULT_PAN')
                """)
                conn.commit()
                
            rows = conn.execute("SELECT id, firm_name, address, gstin, pan FROM offices WHERE is_active = 1").fetchall()
            self.office_data = {} # Map ID to full details
            for row in rows:
                self.office_combo.addItem(row['firm_name'], row['id'])
                # Store structural data for easier access
                self.office_data[row['id']] = {
                    'firm_name': row['firm_name'],
                    'address': row['address'],
                    'gstin': row['gstin'],
                    'pan': row['pan'],
                    'display_text': f"{row['firm_name']}\n{row['address']}\nGSTIN: {row['gstin']} | PAN: {row['pan']}"
                }
        finally:
            conn.close()
            self.office_combo.blockSignals(False)
            self.on_office_changed()

    def on_office_changed(self):
        oid = self.office_combo.currentData()
        if oid in self.office_data:
            self.office_display.setText(self.office_data[oid]['display_text'])
            self.auto_select_tax_type()

    def auto_select_tax_type(self):
        """Auto-select IGST vs CGST_SGST based on first 2 digits of GSTINs"""
        office_id = self.office_combo.currentData()
        client_gstin = self.client_combo.currentData()
        
        if not office_id or not client_gstin or office_id not in self.office_data:
            return
            
        office_gstin = self.office_data[office_id].get('gstin', '')
        
        # GSTIN State codes are the first two digits
        if len(office_gstin) >= 2 and len(client_gstin) >= 2:
            office_state = office_gstin[:2]
            client_state = client_gstin[:2]
            
            self.tax_combo.blockSignals(True)
            if office_state == client_state:
                # Same state -> CGST/SGST
                idx = self.tax_combo.findText("CGST_SGST")
                if idx >= 0: self.tax_combo.setCurrentIndex(idx)
            else:
                # Different state -> IGST
                idx = self.tax_combo.findText("IGST")
                if idx >= 0: self.tax_combo.setCurrentIndex(idx)
            self.tax_combo.blockSignals(False)
    def load_clients(self):
        self.client_combo.clear()
        conn = self.db.get_connection()
        try:
            rows = conn.execute("SELECT gstin, client_name FROM clients").fetchall()
            for row in rows:
                self.client_combo.addItem(f"{row['gstin']} - {row['client_name']}", row['gstin'])
        finally:
            conn.close()
            # Default to no selection so user can search
            self.client_combo.blockSignals(True)
            self.client_combo.setCurrentIndex(-1)
            self.client_combo.blockSignals(False)
            
    def add_item_row(self):
        rc = self.items_table.rowCount()
        if rc >= 5:
            QMessageBox.warning(self, "Limit", "Max 5 line items allowed.")
            return
        self.items_table.insertRow(rc)
        
    def remove_item_row(self):
        rc = self.items_table.rowCount()
        if rc > 0:
            self.items_table.removeRow(rc-1)

    def get_items_data(self):
        items = []
        rows = self.items_table.rowCount()
        for i in range(rows):
            desc = self.items_table.item(i, 0)
            hsn = self.items_table.item(i, 1)
            amt = self.items_table.item(i, 2)
            rate = self.items_table.item(i, 3)
            
            if desc and amt: # Minimal validation
                try:
                    amount_val = float(amt.text())
                    rate_val = float(rate.text()) if rate else 0
                    if rate_val not in [0, 5, 12, 18]:
                         QMessageBox.warning(self, "Error", f"Invalid GST Rate at row {i+1}. Allowed: 0, 5, 12, 18")
                         return None
                    
                    items.append({
                        "description": desc.text(),
                        "hsn_code": hsn.text() if hsn else "",
                        "amount": amount_val,
                        "gst_rate": rate_val
                    })
                except ValueError:
                    QMessageBox.warning(self, "Error", f"Invalid number format at row {i+1}")
                    return None
        if not items:
            QMessageBox.warning(self, "Error", "Please add at least one item.")
            return None
        return items

    def calculate_totals(self):
        items = self.get_items_data()
        if not items:
            return
            
        tax_type = self.tax_combo.currentText()
        taxable = 0.0
        tax_amt = 0.0
        
        for item in items:
            taxable += item['amount']
            rate = item['gst_rate']
            if tax_type != 'NONE':
                tax_amt += item['amount'] * (rate / 100.0)
                
        total = taxable + tax_amt
        self.totals_label.setText(f"Taxable: {taxable:.2f} | Tax: {tax_amt:.2f} | Grand Total: {total:.2f}")
        return taxable, tax_amt, total

    def load_banks(self):
        self.bank_combo.blockSignals(True)
        self.bank_combo.clear()
        conn = self.db.get_connection()
        try:
            # Get distinct bank names
            rows = conn.execute("SELECT DISTINCT bank_name FROM branches ORDER BY bank_name").fetchall()
            self.bank_combo.addItem("Select Bank", "")
            for row in rows:
                self.bank_combo.addItem(row['bank_name'], row['bank_name'])
        finally:
            conn.close()
            self.bank_combo.blockSignals(False)

    def load_bank_cities(self, bank_name):
        self.city_combo.blockSignals(True)
        self.city_combo.clear()
        self.branch_combo.clear()
        
        if not bank_name or bank_name == "Select Bank":
             self.city_combo.blockSignals(False)
             return
             
        conn = self.db.get_connection()
        try:
            rows = conn.execute("SELECT DISTINCT city FROM branches WHERE bank_name = ? ORDER BY city", (bank_name,)).fetchall()
            self.city_combo.addItem("Select City", "")
            for row in rows:
                self.city_combo.addItem(row['city'], row['city'])
        finally:
            conn.close()
            self.city_combo.blockSignals(False)
            
    def load_bank_branches(self, city):
        self.branch_combo.blockSignals(True)
        self.branch_combo.clear()
        
        bank_name = self.bank_combo.currentText()
        if not city or city == "Select City" or not bank_name:
            self.branch_combo.blockSignals(False)
            return

        conn = self.db.get_connection()
        try:
            # We want branch name
            rows = conn.execute("SELECT branch_name, ifsc_code FROM branches WHERE bank_name = ? AND city = ?", (bank_name, city)).fetchall()
            self.branch_combo.addItem("Select Branch", "")
            for row in rows:
                # Store IFSC or ID if needed, but text is fine for display
                if row['ifsc_code']:
                    display = f"{row['branch_name']} ({row['ifsc_code']})"
                else:
                    display = row['branch_name']
                self.branch_combo.addItem(display, row['branch_name'])
        finally:
            conn.close()
            self.branch_combo.blockSignals(False)
    def generate_invoice(self):
        cli_data = self.client_combo.currentText()
        if not cli_data:
            QMessageBox.warning(self, "Error", "Select a client.")
            return
            
        client_gstin = self.client_combo.currentData()
        office_id = self.office_combo.currentData()
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        tax_type = self.tax_combo.currentText()
        
        # Get selected bank details (Use currentText/Data from combo boxes)
        bank = self.bank_combo.currentText()
        city = self.city_combo.currentText()
        branch_data = self.branch_combo.currentText() # This has "Name (IFSC)"
        
        # We need raw values for the invoice footer
        # If user picked "Select Bank", treat as empty
        if bank == "Select Bank": bank = ""
        if city == "Select City": city = ""
        if branch_data == "Select Branch": 
            branch = ""
        else:
            # Extract just the branch name if needed, or keep full string?
            # User likely wants "Belathur" not "Belathur (IFSC)" in the "Allotted By..." text 
            # if the PDF expects just name. Let's send what's in the box, or split.
            # actually previously I used .split('(')[0]
            branch = branch_data.split('(')[0].strip()

        allotted = {
            'bank': bank,
            'branch': branch,
            'city': city,
            'pos': self.pos_combo.currentText().strip()
        }
        
        items = self.get_items_data()
        if not items:
            return
            
        try:
            import os
            import shutil
            
            if self.editing_invoice_id:
                # --- UPDATE MODE ---
                inv_id = self.editing_invoice_id
                
                # 1. Get current details for archival
                conn = self.db.get_connection()
                try:
                    old_inv = conn.execute("SELECT invoice_number, pdf_path FROM invoices WHERE id=?", (inv_id,)).fetchone()
                    invoice_number = old_inv['invoice_number']
                    old_pdf_path = old_inv['pdf_path']
                    
                    # 2. Archive existing PDF if it exists
                    if old_pdf_path and os.path.exists(old_pdf_path):
                        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                        deleted_dir = os.path.join(desktop, "AnkitaCA", "Generated Invoices", "DELETED_Invoices")
                        if not os.path.exists(deleted_dir):
                            os.makedirs(deleted_dir)
                            
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        archived_name = f"{timestamp}_{os.path.basename(old_pdf_path)}"
                        archived_path = os.path.join(deleted_dir, archived_name)
                        
                        try:
                            shutil.copy2(old_pdf_path, archived_path)
                            print(f"Old PDF archived to: {archived_path}")
                        except Exception as e:
                            print(f"Archival failed: {e}")

                    # 3. Update DB Record (Recalculate totals)
                    taxable_total = sum(float(item['amount']) for item in items)
                    cgst_total = sgst_total = igst_total = 0.0
                    for item in items:
                        amt = float(item['amount'])
                        rate = float(item['gst_rate'])
                        tax_val = amt * (rate / 100.0)
                        if tax_type == 'IGST':
                            igst_total += tax_val
                        elif tax_type == 'CGST_SGST':
                            cgst_total += tax_val / 2
                            sgst_total += tax_val / 2
                    
                    grand_total = taxable_total + cgst_total + sgst_total + igst_total
                    
                    conn.execute("""
                        UPDATE invoices SET 
                            client_gstin=?, office_id=?, invoice_date=?, tax_type=?,
                            taxable_value=?, cgst_amount=?, sgst_amount=?, igst_amount=?, grand_total=?,
                            allotted_bank=?, allotted_branch=?, allotted_city=?, place_of_supply=?,
                            status = CASE WHEN status = 'Cancelled' THEN 'Generated' ELSE status END
                        WHERE id=?
                    """, (client_gstin, office_id, date_str, tax_type, taxable_total, cgst_total, 
                          sgst_total, igst_total, grand_total, bank, branch, city, allotted['pos'], inv_id))
                    
                    # 4. Update items
                    conn.execute("DELETE FROM invoice_items WHERE invoice_id=?", (inv_id,))
                    for item in items:
                        conn.execute("""
                            INSERT INTO invoice_items (invoice_id, description, hsn_code, amount, gst_rate)
                            VALUES (?, ?, ?, ?, ?)
                        """, (inv_id, item['description'], item['hsn_code'], item['amount'], item['gst_rate']))
                    
                    conn.commit()
                finally:
                    conn.close()
                
                # 5. Regenerate PDF
                inv_details = self.invoice_service.get_invoice_details(inv_id)
                pdf_path = self.pdf_generator.generate(inv_details)
                
                # Update path in DB
                conn = self.db.get_connection()
                conn.execute("UPDATE invoices SET pdf_path=? WHERE id=?", (pdf_path, inv_id))
                conn.commit()
                conn.close()
                
                # Reset editing state
                self.editing_invoice_id = None
                success_msg = f"Invoice {invoice_number} Updated Successfully!"

            else:
                # --- CREATE MODE ---
                # Create DB Entry
                inv_id, invoice_number = self.invoice_service.create_invoice(
                    client_gstin, office_id, date_str, items, tax_type, allotted_details=allotted
                )
                
                # Generate PDF
                inv_details = self.invoice_service.get_invoice_details(inv_id)
                pdf_path = self.pdf_generator.generate(inv_details)
                
                # Save PDF path to DB
                conn = self.db.get_connection()
                conn.execute("UPDATE invoices SET pdf_path = ? WHERE id = ?", (pdf_path, inv_id))
                conn.commit()
                conn.close()
                success_msg = f"Invoice {invoice_number} Generated Successfully!"
            
            # --- Common Post-Processing (Downloads & Opening) ---
            if pdf_path:
                filename = os.path.basename(pdf_path)
                downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
                saved_to_downloads = False
                
                try:
                    target_file = os.path.join(downloads_path, filename)
                    shutil.copy2(pdf_path, target_file)
                    saved_to_downloads = True
                except Exception as e:
                    print(f"Failed to copy to downloads: {e}")

                # Show Success Message
                display_msg = success_msg
                if saved_to_downloads:
                    display_msg += f"\n\nSaved to DOWNLOADS folder:\n{filename}"
                else:
                    display_msg += f"\n\nSaved at:\n{pdf_path}"
                    
                QMessageBox.information(self, "Success", display_msg)
                
                # Auto-open
                open_target = target_file if saved_to_downloads else pdf_path
                if open_target and os.path.exists(open_target):
                    try:
                        QDesktopServices.openUrl(QUrl.fromLocalFile(open_target))
                    except Exception as e:
                        print(f"Could not open PDF: {e}")
            
            # Clear Form
            self.items_table.setRowCount(0)
            self.items_table.insertRow(0)
            self.totals_label.setText("Taxable: 0.00 | Tax: 0.00 | Grand Total: 0.00")
            
            # Notify that processing is done
            self.invoice_processed.emit()
            
        except ValueError as e:
            QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creating invoice: {str(e)}")
    
    def skip_invoice_number(self):
        """Skip the next invoice number by creating a dummy 'Cancelled' invoice"""
        try:
            # Get what the next invoice number would be
            date_obj = self.date_edit.date().toPython()
            next_invoice_num, next_serial = self.invoice_service.generate_invoice_number(date_obj)
            
            reply = QMessageBox.question(
                self, 
                "Generate Dummy Invoice", 
                f"This will generate a dummy invoice for number:\n{next_invoice_num}\n\n"
                f"A placeholder 'Cancelled' invoice will be created to maintain the sequence.\n\n"
                f"Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            
            # Create a dummy cancelled invoice to reserve the number
            conn = self.db.get_connection()
            
            # Get required data
            office_id = self.office_combo.currentData() or 1
            client_gstin = "SKIP00000000000"  # Dummy GSTIN
            
            # Check if dummy client exists, if not create it
            existing = conn.execute("SELECT gstin FROM clients WHERE gstin=?", (client_gstin,)).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO clients (gstin, client_name, address) VALUES (?, ?, ?)",
                    (client_gstin, "SKIPPED INVOICE", "N/A")
                )
            
            fy = self.invoice_service.get_financial_year(date_obj)
            month_str = date_obj.strftime("%m")
            date_str = date_obj.strftime("%Y-%m-%d")
            
            # Insert dummy invoice with Cancelled status
            cursor = conn.execute("""
                INSERT INTO invoices (
                    invoice_number, invoice_date, financial_year, month_str, serial_number,
                    client_gstin, office_id, tax_type, taxable_value, cgst_amount, sgst_amount,
                    igst_amount, grand_total, status, place_of_supply
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                next_invoice_num, date_str, fy, month_str, next_serial,
                client_gstin, office_id, 'NONE', 0.0, 0.0, 0.0, 0.0, 0.0,
                'Cancelled', 'N/A'
            ))
            
            # Get the invoice ID and add a placeholder item
            invoice_id = cursor.lastrowid
            conn.execute("""
                INSERT INTO invoice_items (invoice_id, description, hsn_code, amount, gst_rate)
                VALUES (?, ?, ?, ?, ?)
            """, (invoice_id, "PLACEHOLDER - Invoice number reserved for future use", "", 0.0, 0))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(
                self, 
                "Success", 
                f"Dummy invoice number {next_invoice_num} has been generated.\n\n"
                f"Next invoice will be: {self.get_next_invoice_preview()}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to skip invoice number: {str(e)}")
    
    def get_next_invoice_preview(self):
        """Get preview of what the next invoice number will be"""
        try:
            date_obj = self.date_edit.date().toPython()
            next_num, _ = self.invoice_service.generate_invoice_number(date_obj)
            return next_num
        except:
            return "Unknown"
    
    def load_invoice_for_edit(self, invoice_id):
        """Load an existing invoice for editing"""
        conn = self.db.get_connection()
        try:
            # Fetch invoice data
            invoice = conn.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
            if not invoice:
                QMessageBox.warning(self, "Error", "Invoice not found")
                return
            
            # Fetch invoice items
            items = conn.execute("SELECT * FROM invoice_items WHERE invoice_id=? ORDER BY id", (invoice_id,)).fetchall()
            
            # Store the invoice ID we're editing
            self.editing_invoice_id = invoice_id
            
            # Update title
            self.title_label.setText(f"UPDATING INVOICE # {invoice['invoice_number']}")
            self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #E91E63; margin-bottom: 10px;")
            
            # Populate form fields
            # We block signals during population to avoid redundant cascading loads
            self.office_combo.blockSignals(True)
            self.client_combo.blockSignals(True)
            self.date_edit.blockSignals(True)
            self.pos_combo.blockSignals(True)
            self.bank_combo.blockSignals(True)
            self.city_combo.blockSignals(True)
            self.branch_combo.blockSignals(True)
            
            try:
                # Office
                for i in range(self.office_combo.count()):
                    if str(self.office_combo.itemData(i)) == str(invoice['office_id']):
                        self.office_combo.setCurrentIndex(i)
                        break
                
                # Client
                for i in range(self.client_combo.count()):
                    if str(self.client_combo.itemData(i)) == str(invoice['client_gstin']):
                        self.client_combo.setCurrentIndex(i)
                        break
                
                # Date
                try:
                    date_obj = datetime.datetime.strptime(invoice['invoice_date'], '%Y-%m-%d').date()
                    self.date_edit.setDate(QDate(date_obj.year, date_obj.month, date_obj.day))
                except Exception as e:
                    print(f"Date parse error: {e}")
                
                # POS
                if invoice['place_of_supply']:
                    for i in range(self.pos_combo.count()):
                        if self.pos_combo.itemText(i) == invoice['place_of_supply']:
                            self.pos_combo.setCurrentIndex(i)
                            break
                
                # Bank details (Cascading)
                if invoice['allotted_bank']:
                    # 1. Load and Select Bank
                    for i in range(self.bank_combo.count()):
                        if self.bank_combo.itemText(i) == invoice['allotted_bank']:
                            self.bank_combo.setCurrentIndex(i)
                            break
                    
                    # 2. Load Cities for this bank and Select
                    self.load_bank_cities(invoice['allotted_bank'])
                    if invoice['allotted_city']:
                        for i in range(self.city_combo.count()):
                            if self.city_combo.itemText(i) == invoice['allotted_city']:
                                self.city_combo.setCurrentIndex(i)
                                break
                    
                    # 3. Load Branches for this city and Select
                    self.load_bank_branches(invoice['allotted_city'])
                    if invoice['allotted_branch']:
                        for i in range(self.branch_combo.count()):
                             # Note: branch_combo itemData is the branch name
                             if self.branch_combo.itemData(i) == invoice['allotted_branch']:
                                  self.branch_combo.setCurrentIndex(i)
                                  break
            finally:
                # Always restore signals
                self.office_combo.blockSignals(False)
                self.client_combo.blockSignals(False)
                self.date_edit.blockSignals(False)
                self.pos_combo.blockSignals(False)
                self.bank_combo.blockSignals(False)
                self.city_combo.blockSignals(False)
                self.branch_combo.blockSignals(False)
            
            # Load items into table
            self.items_table.setRowCount(0)
            for item in items:
                row = self.items_table.rowCount()
                self.items_table.insertRow(row)
                self.items_table.setItem(row, 0, QTableWidgetItem(item['description']))
                self.items_table.setItem(row, 1, QTableWidgetItem(item['hsn_code'] or ""))
                self.items_table.setItem(row, 2, QTableWidgetItem(str(item['amount'])))
                self.items_table.setItem(row, 3, QTableWidgetItem(str(item['gst_rate'])))
            
            # Update totals
            self.calculate_totals()
            
            # Removed redundant QMessageBox - title label handles it.
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load invoice: {str(e)}")
        finally:
            conn.close()

