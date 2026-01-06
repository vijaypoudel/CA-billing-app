import sqlite3
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QHBoxLayout, 
                               QLineEdit, QPushButton, QMessageBox, QLabel, 
                               QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView, QMenu, QFrame)
from PySide6.QtGui import QAction
from PySide6.QtCore import Slot, Qt
from db.database import db_manager
from services.fuzzy_match_service import FuzzyMatchService

class BranchMaster(QWidget):
    def __init__(self):
        super().__init__()
        self.db = db_manager
        self.fuzzy = FuzzyMatchService()
        self.current_id = None
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)
        
        # 1. Bank Card (Form)
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

        # Row 1: Branch, Bank, City
        row1_layout = QHBoxLayout()
        self.name_input = self.create_input_group(row1_layout, "Branch Name", "e.g. MG Road", is_row=True)
        self.name_input.textChanged.connect(self.check_similarity)
        self.bank_name_input = self.create_input_group(row1_layout, "Bank Name", "e.g. HDFC", is_row=True)
        self.city_input = self.create_input_group(row1_layout, "City", "e.g. Bangalore", is_row=True)
        card_layout.addLayout(row1_layout)

        # Row 2: IFSC, Acc No
        row2_layout = QHBoxLayout()
        self.ifsc_input = self.create_input_group(row2_layout, "IFSC Code", "IFSC Code", is_row=True)
        self.acc_input = self.create_input_group(row2_layout, "Account No", "Account Number", is_row=True)
        card_layout.addLayout(row2_layout)
        
        self.suggestion_lbl = QLabel("")
        self.suggestion_lbl.setStyleSheet("color: #E67E22; font-style: italic; font-size: 11px;")
        card_layout.addWidget(self.suggestion_lbl)
        
        # Buttons
        fbtn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Save Bank Details")
        self.add_btn.setFixedHeight(35)
        self.add_btn.clicked.connect(self.add_branch)
        self.add_btn.setStyleSheet("""
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
        
        fbtn_layout.addWidget(self.add_btn)
        fbtn_layout.addWidget(self.clear_btn)
        fbtn_layout.addStretch()
        card_layout.addLayout(fbtn_layout)
        self.main_layout.addWidget(form_card)
        
        # 2. Directory Header
        self.main_layout.addWidget(QLabel("<b>Registered Branches:</b>"))
        
        # 3. Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Branch", "City", "Bank", "IFSC", "Account", "Actions"])
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

    @Slot(str)
    def check_similarity(self, text):
        if len(text) < 3:
            self.suggestion_lbl.setText("")
            return
        conn = self.db.get_connection()
        try:
            rows = conn.execute("SELECT branch_name FROM branches").fetchall()
            existing = [r['branch_name'] for r in rows]
            matches = self.fuzzy.get_similar_branches(text, existing)
            self.suggestion_lbl.setText(f"Similar: {', '.join([m[0] for m in matches[:2]])}" if matches else "")
        finally: conn.close()

    def add_branch(self):
        name, city, bank = self.name_input.text().strip(), self.city_input.text().strip(), self.bank_name_input.text().strip()
        ifsc = self.ifsc_input.text().strip()
        acc = self.acc_input.text().strip()
        
        if not all([name, city, bank]):
            QMessageBox.warning(self, "Error", "Name, City, and Bank are required.")
            return
        conn = self.db.get_connection()
        try:
            if self.current_id:
                conn.execute("UPDATE branches SET branch_name=?, city=?, bank_name=?, ifsc_code=?, account_number=? WHERE id=?", 
                             (name, city, bank, ifsc, acc, self.current_id))
            else:
                conn.execute("INSERT INTO branches (branch_name, city, bank_name, ifsc_code, account_number) VALUES (?, ?, ?, ?, ?)", 
                             (name, city, bank, ifsc, acc))
            conn.commit()
            self.clear_form()
            self.refresh_table()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))
        finally: conn.close()

    def refresh_table(self):
        self.table.setRowCount(0)
        conn = self.db.get_connection()
        try:
            rows = conn.execute("SELECT * FROM branches ORDER BY bank_name").fetchall()
            for r_idx, row in enumerate(rows):
                self.table.insertRow(r_idx)
                for c_idx, key in enumerate(['id', 'branch_name', 'city', 'bank_name', 'ifsc_code', 'account_number']):
                    self.table.setItem(r_idx, c_idx, QTableWidgetItem(str(row[key])))
                
                actions_btn = QPushButton("Actions")
                actions_btn.setStyleSheet("padding: 2px; background: #f8f9fa; border: 1px solid #ddd;")
                
                menu = QMenu(actions_btn)
                edit_act = QAction("Edit", menu)
                edit_act.triggered.connect(lambda checked=False, r=r_idx: self.load_for_editing(r))
                
                del_act = QAction("Delete", menu)
                branch_id = row['id']
                del_act.triggered.connect(lambda checked=False, i=branch_id: self.delete_branch(i))
                
                menu.addAction(edit_act)
                menu.addAction(del_act)
                actions_btn.setMenu(menu)
                # Action column is 6
                self.table.setCellWidget(r_idx, 6, actions_btn)
        finally: conn.close()

    def load_for_editing(self, row):
        self.current_id = self.table.item(row, 0).text()
        self.name_input.setText(self.table.item(row, 1).text())
        self.city_input.setText(self.table.item(row, 2).text())
        self.bank_name_input.setText(self.table.item(row, 3).text())
        self.ifsc_input.setText(self.table.item(row, 4).text())
        self.acc_input.setText(self.table.item(row, 5).text())
        
        self.add_btn.setText("Update Branch")
        self.add_btn.setStyleSheet("background-color: #E67E22; color: white; font-weight: bold; padding: 0 20px; border-radius: 4px; height: 35px;")

    def delete_branch(self, branch_id):
        if QMessageBox.question(self, "Delete", "Delete this branch?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            conn = self.db.get_connection()
            try:
                conn.execute("DELETE FROM branches WHERE id=?", (branch_id,))
                conn.commit()
                self.refresh_table()
                if self.current_id == str(branch_id): self.clear_form()
            finally: conn.close()

    def clear_form(self):
        self.current_id = None
        self.name_input.clear()
        self.bank_name_input.clear()
        self.city_input.clear()
        self.ifsc_input.clear()
        self.acc_input.clear()
        self.add_btn.setText("Save Bank Details")
        self.add_btn.setStyleSheet("background-color: #3498DB; color: white; font-weight: bold; padding: 0 20px; border-radius: 4px; height: 35px;")
