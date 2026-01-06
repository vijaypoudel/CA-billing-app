import sqlite3
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLineEdit, QPushButton, QMessageBox, QLabel, 
                               QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QFrame)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from db.database import db_manager
from utils.validators import validate_gstin

class ClientMaster(QWidget):
    def __init__(self):
        super().__init__()
        self.db = db_manager
        self.current_gstin = None
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)
        
        # 1. Client Card (Form)
        form_card = QFrame()
        form_card.setObjectName("FormCard")
        form_card.setStyleSheet("""
            #FormCard {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        card_layout = QVBoxLayout(form_card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(10)

        # Row 1: Name, GST, Phone
        row1_layout = QHBoxLayout()
        self.name_input = self.create_input_group(row1_layout, "Client Name", "Legal/Trade Name", is_row=True)
        self.gstin_input = self.create_input_group(row1_layout, "GSTIN", "15-digit GSTIN", is_row=True)
        self.phone_input = self.create_input_group(row1_layout, "Phone", "10-digit Number", is_row=True)
        card_layout.addLayout(row1_layout)

        # Row 2: Address
        self.address_input = self.create_input_group(card_layout, "Billing Address", "Full Address")
        
        # Row 3: Email
        self.email_input = self.create_input_group(card_layout, "Email Address", "contact@client.com")

        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Client")
        self.save_btn.setFixedHeight(35)
        self.save_btn.clicked.connect(self.save_client)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB; 
                color: white; 
                font-weight: bold; 
                padding: 0 20px; 
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #2980B9; }
        """)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedHeight(35)
        self.clear_btn.clicked.connect(self.clear_form)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1; 
                color: #2c3e50; 
                padding: 0 20px; 
                border-radius: 4px;
                border: 1px solid #bdc3c7;
            }
            QPushButton:hover { background-color: #dfe6e9; }
        """)
        
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        card_layout.addLayout(btn_layout)
        
        self.main_layout.addWidget(form_card)

        # 2. Search & Directory Header
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("<b>Client Directory:</b>"))
        search_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search Client Name...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdde1;
                border-radius: 15px;
                padding: 5px 15px;
                background-color: #fff;
            }
        """)
        search_layout.addWidget(self.search_input)
        self.main_layout.addLayout(search_layout)
        
        # 3. High-Density Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["GSTIN", "Name", "Address", "Email", "Phone", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("QTableWidget { border: 1px solid #e0e0e0; border-radius: 4px; }")
        self.main_layout.addWidget(self.table)
        
        self.refresh_table()

    def create_input_group(self, parent_layout, label_text, placeholder, is_row=False):
        group = QVBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet("font-weight: bold; color: #34495e; font-size: 11px;")
        
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setFixedHeight(30)
        line_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdde1;
                border-radius: 4px;
                padding: 0 8px;
                background-color: #fdfdfd;
            }
            QLineEdit:focus { border: 1px solid #3498DB; }
        """)
        
        group.addWidget(lbl)
        group.addWidget(line_edit)
        
        if is_row:
            container = QWidget()
            container.setLayout(group)
            parent_layout.addWidget(container)
        else:
            parent_layout.addLayout(group)
        return line_edit

    def filter_table(self, text):
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 1) # Client Name column
            match = text.lower() in item.text().lower()
            self.table.setRowHidden(i, not match)

    def save_client(self):
        gstin = self.gstin_input.text().strip().upper()
        name = self.name_input.text().strip()
        address = self.address_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        
        if not gstin or not name:
            QMessageBox.warning(self, "Error", "GSTIN and Name are required.")
            return
        if not validate_gstin(gstin):
             QMessageBox.warning(self, "Error", "Invalid GSTIN.")
             return
            
        conn = self.db.get_connection()
        try:
            if self.current_gstin:
                conn.execute("UPDATE clients SET gstin=?, client_name=?, address=?, email=?, phone=? WHERE gstin=?", 
                             (gstin, name, address, email, phone, self.current_gstin))
            else:
                conn.execute("INSERT INTO clients VALUES (?, ?, ?, ?, ?)", 
                             (gstin, name, address, email, phone))
            conn.commit()
            self.clear_form()
            self.refresh_table()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))
        finally: conn.close()

    def refresh_table(self):
        self.table.setRowCount(0)
        conn = self.db.get_connection()
        try:
            rows = conn.execute("SELECT * FROM clients ORDER BY client_name").fetchall()
            for r_idx, row in enumerate(rows):
                self.table.insertRow(r_idx)
                for c_idx, key in enumerate(['gstin', 'client_name', 'address', 'email', 'phone']):
                    self.table.setItem(r_idx, c_idx, QTableWidgetItem(str(row[key])))
                
                # Actions Menu
                actions_btn = QPushButton("Actions")
                actions_btn.setStyleSheet("padding: 2px; background: #f8f9fa; border: 1px solid #ddd;")
                
                menu = QMenu(actions_btn)
                edit_act = QAction("Edit", menu)
                # Need to use row index for load_for_editing, but r_idx changes. 
                # Safer to pass specific GSTIN or use a captured index correctly.
                edit_act.triggered.connect(lambda checked=False, r=r_idx: self.load_for_editing(r))
                
                del_act = QAction("Delete", menu)
                client_gstin = row['gstin']
                del_act.triggered.connect(lambda checked=False, g=client_gstin: self.delete_client(g))
                
                menu.addAction(edit_act)
                menu.addAction(del_act)
                actions_btn.setMenu(menu)
                self.table.setCellWidget(r_idx, 5, actions_btn)
        finally: conn.close()
        self.filter_table(self.search_input.text())

    def load_for_editing(self, row):
        self.current_gstin = self.table.item(row, 0).text()
        self.gstin_input.setText(self.current_gstin)
        self.name_input.setText(self.table.item(row, 1).text())
        self.address_input.setText(self.table.item(row, 2).text())
        self.email_input.setText(self.table.item(row, 3).text())
        self.phone_input.setText(self.table.item(row, 4).text())
        
        self.save_btn.setText("Update Client")
        self.save_btn.setStyleSheet("background-color: #E67E22; color: white; font-weight: bold; padding: 0 20px; border-radius: 4px; height: 35px;")

    def delete_client(self, gstin):
        if QMessageBox.question(self, "Delete", f"Delete client {gstin}?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            conn = self.db.get_connection()
            try:
                conn.execute("DELETE FROM clients WHERE gstin=?", (gstin,))
                conn.commit()
                self.refresh_table()
                if self.current_gstin == gstin: self.clear_form()
            finally: conn.close()

    def clear_form(self):
        self.current_gstin = None
        self.gstin_input.clear()
        self.name_input.clear()
        self.address_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.save_btn.setText("Save Client")
        self.save_btn.setStyleSheet("background-color: #3498DB; color: white; font-weight: bold; padding: 0 20px; border-radius: 4px; height: 35px;")
