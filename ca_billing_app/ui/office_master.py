import sqlite3
import os
import sys
import platform
import shutil
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QLineEdit, QPushButton, QMessageBox, QLabel, 
                               QGroupBox, QScrollArea, QFrame, QFileDialog, QTextEdit)
from PySide6.QtCore import Qt, Slot
from db.database import db_manager
from config_manager import config_manager
import subprocess

DEFAULT_DECLARATION = (
    "1. All the details mentioned in the invoice are true and correct.\n"
    "2. Please transfer the fee in our Account- Ankita Agarwal & Associates\n"
    "maintained at Bank of Baroda, IFSC: BARB0DILSHA Account No.\n"
    "31680200002026."
)

class OfficeMaster(QWidget):
    def __init__(self):
        super().__init__()
        self.db = db_manager
        self.current_id = None
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)
        
        # 1. Firm Details Card (Form)
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
        
        # Row 1: Name, GST, PAN
        row1_layout = QHBoxLayout()
        self.firm_name_input = self.create_input_group(row1_layout, "Firm Name", "e.g. ANKITA AGARWAL & ASSOCIATES", is_row=True)
        self.gstin_input = self.create_input_group(row1_layout, "GSTIN", "15-digit GSTIN", is_row=True)
        self.pan_input = self.create_input_group(row1_layout, "PAN", "10-digit PAN", is_row=True)
        card_layout.addLayout(row1_layout)
        
        # Row 2: Address
        self.address_input = self.create_input_group(card_layout, "Full Address", "Complete address for billing")
        
        # Row 3: Email & Invoice Formatting
        row3_layout = QHBoxLayout()
        self.email_input = self.create_input_group(row3_layout, "Email Address", "Email for reports/backups", is_row=True)
        self.invoice_format_input = self.create_input_group(row3_layout, "Invoice Number Format", "e.g. A4CA/{FY}/{MM}/{SEQ}", is_row=True)
        self.invoice_format_input.setText("A4CA/{FY}/{MM}/{SEQ}")
        self.initial_serial_input = self.create_input_group(row3_layout, "Initial Serial Number", "Start from (e.g. 0)", is_row=True)
        self.initial_serial_input.setText("0")
        card_layout.addLayout(row3_layout)
        
        # Helper text for formats
        help_text = (
            "<b>Format Variables:</b> {FY} = Fin. Year (2526), {MM} = Month (04), {SEQ} = Serial (001)<br>"
            "<b>Examples:</b><br>"
            "• Type <b>A4CA/{FY}/{MM}/{SEQ}</b> to get <i>A4CA/2526/04/001</i><br>"
            "• Type <b>DEL/{FY}/{MM}{SEQ}</b> to get <i>DEL/2526/04001</i><br>"
            "• Type <b>MUMBAI-{SEQ}</b> to get <i>MUMBAI-001</i>"
        )
        help_label = QLabel(help_text)
        help_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        card_layout.addWidget(help_label)
        
        # Real-time preview label
        self.preview_label = QLabel("Preview: A4CA/2526/04/001")
        self.preview_label.setStyleSheet("color: #27ae60; font-size: 13px; font-weight: bold; margin-bottom: 5px;")
        card_layout.addWidget(self.preview_label)
        
        # Connect signals for live preview
        self.invoice_format_input.textChanged.connect(self.update_preview)
        self.initial_serial_input.textChanged.connect(self.update_preview)
        
        # Row 4: Declaration (multi-line)
        decl_lbl = QLabel("Default Declaration Text")
        decl_lbl.setStyleSheet("font-weight: bold; color: #34495e; font-size: 12px;")
        self.declaration_input = QTextEdit()
        self.declaration_input.setPlaceholderText(
            "Enter the default declaration text that will appear on every invoice...\n"
            "e.g. 1. All details are true and correct.\n"
            "2. Please transfer the fee to Account No. XXXX..."
        )
        self.declaration_input.setMinimumHeight(90)
        self.declaration_input.setMaximumHeight(120)
        self.declaration_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdde1;
                border-radius: 5px;
                padding: 6px 10px;
                background-color: #fcfcfc;
                font-size: 12px;
            }
            QTextEdit:focus { border: 1px solid #3498DB; background-color: #fff; }
        """)
        card_layout.addWidget(decl_lbl)
        card_layout.addWidget(self.declaration_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Business Profile")
        self.save_btn.setFixedHeight(35)
        self.save_btn.clicked.connect(self.save_office)
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
        
        # Compact Backup Scheduler in same row as buttons to save space
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addSpacing(20)
        
        # Inline Scheduler
        sched_lbl = QLabel("🛡️ Daily Tasks:")
        sched_lbl.setStyleSheet("color: #27AE60; font-weight: bold; font-size: 11px;")
        self.sched_btn = QPushButton("Enable Scheduler")
        self.sched_btn.clicked.connect(self.enable_scheduler)
        self.sched_btn.setFixedHeight(30)
        self.sched_btn.setStyleSheet("background-color: #27AE60; color: white; font-size: 11px; padding: 0 10px; border-radius: 4px;")
        
        btn_layout.addWidget(sched_lbl)
        btn_layout.addWidget(self.sched_btn)
        btn_layout.addStretch()
        card_layout.addLayout(btn_layout)
        
        self.main_layout.addWidget(form_card)

        # 2. Data Storage Management Card
        storage_card = QFrame()
        storage_card.setObjectName("StorageCard")
        storage_card.setStyleSheet("""
            #StorageCard {
                background-color: #f4f7f6;
                border: 1px solid #d1d8d7;
                border-radius: 8px;
            }
        """)
        storage_layout = QVBoxLayout(storage_card)
        storage_layout.setContentsMargins(15, 10, 15, 10)
        storage_layout.setSpacing(5)
        
        storage_header = QHBoxLayout()
        storage_title = QLabel("📂 Data Storage Cabinet")
        storage_title.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
        storage_header.addWidget(storage_title)
        storage_header.addStretch()
        
        # Cloud Sync Status
        self.sync_status_lbl = QLabel("")
        storage_header.addWidget(self.sync_status_lbl)
        storage_layout.addLayout(storage_header)
        
        path_layout = QHBoxLayout()
        self.db_path_lbl = QLabel(f"Current Database Path: {config_manager.get_db_path()}")
        self.db_path_lbl.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        self.db_path_lbl.setWordWrap(True)
        
        self.change_path_btn = QPushButton("Move Database")
        self.change_path_btn.setFixedHeight(30)
        self.change_path_btn.clicked.connect(self.change_db_location)
        self.change_path_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e; color: white; border-radius: 4px; padding: 0 15px; font-size: 11px;
            }
            QPushButton:hover { background-color: #2c3e50; }
        """)
        
        path_layout.addWidget(self.db_path_lbl, 3)
        path_layout.addWidget(self.change_path_btn, 1)
        storage_layout.addLayout(path_layout)

        # -- Invoice Storage Folder Row --
        inv_path_layout = QHBoxLayout()
        self.storage_folder_lbl = QLabel(f"Invoice Output Folder: {config_manager.get_storage_folder()}")
        self.storage_folder_lbl.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        self.storage_folder_lbl.setWordWrap(True)
        
        self.change_storage_btn = QPushButton("📁 Change Folder")
        self.change_storage_btn.setFixedHeight(30)
        self.change_storage_btn.clicked.connect(self.change_storage_folder)
        self.change_storage_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60; color: white; border-radius: 4px; padding: 0 15px; font-size: 11px;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        inv_path_layout.addWidget(self.storage_folder_lbl, 3)
        inv_path_layout.addWidget(self.change_storage_btn, 1)
        storage_layout.addLayout(inv_path_layout)
        
        self.main_layout.addWidget(storage_card)
        self.update_sync_status()

        # 3. Existing Sections View
        self.main_layout.addWidget(QLabel("<b>Saved Business Profiles:</b>"))
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.card_container = QWidget()
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(10)
        self.card_layout.addStretch()
        
        self.scroll_area.setWidget(self.card_container)
        self.main_layout.addWidget(self.scroll_area)
        
        self.load_data()

    def update_sync_status(self):
        path = config_manager.get_db_path().lower()
        if "google drive" in path or "g:" in path or "googledrive" in path:
            self.sync_status_lbl.setText("☁️ Google Drive Synced")
            self.sync_status_lbl.setStyleSheet("color: #3498DB; font-weight: bold; font-size: 11px;")
        elif "onedrive" in path:
            self.sync_status_lbl.setText("☁️ OneDrive Synced")
            self.sync_status_lbl.setStyleSheet("color: #0078D4; font-weight: bold; font-size: 11px;")
        elif "dropbox" in path:
            self.sync_status_lbl.setText("☁️ Dropbox Synced")
            self.sync_status_lbl.setStyleSheet("color: #0061FF; font-weight: bold; font-size: 11px;")
        else:
            self.sync_status_lbl.setText("💾 Local Storage")
            self.sync_status_lbl.setStyleSheet("color: #7f8c8d; font-size: 11px;")

    def _check_backup_safety(self, path):
        """
        Returns (is_safe: bool, label: str) based on whether path appears
        to be inside a cloud-synced directory.
        """
        p = path.lower()
        cloud_hints = [
            ("google drive", "☁️ Google Drive"),
            ("googledrive", "☁️ Google Drive"),
            ("onedrive", "☁️ OneDrive"),
            ("dropbox", "☁️ Dropbox"),
            ("icloud", "☁️ iCloud"),
            ("mobile documents", "☁️ iCloud"),  # macOS iCloud path
            ("box sync", "☁️ Box"),
            ("pcloud", "☁️ pCloud"),
        ]
        for hint, label in cloud_hints:
            if hint in p:
                return True, label
        return False, "💾 Local Storage (No Backup Detected)"

    def change_storage_folder(self):
        new_dir = QFileDialog.getExistingDirectory(
            self, "Select Invoice Output Folder", config_manager.get_storage_folder()
        )
        if not new_dir:
            return

        is_safe, backup_label = self._check_backup_safety(new_dir)
        if not is_safe:
            reply = QMessageBox.warning(
                self, "⚠️ Backup Risk — Please Read Carefully",
                "<b>The folder you selected does not appear to be backed up to the cloud.</b><br><br>"
                "Invoices are critical financial records. If your computer is lost, damaged, or "
                "stolen, you will lose all your invoices permanently.<br><br>"
                "<b>We strongly recommend choosing a folder inside:</b><br>"
                "• Google Drive<br>• OneDrive<br>• Dropbox<br>• iCloud Drive<br><br>"
                "Are you sure you want to use this local folder? <b>You accept full responsibility "
                "for backing up your invoices.</b>",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        config_manager.set_storage_folder(new_dir)
        self.storage_folder_lbl.setText(f"Invoice Output Folder: {new_dir}  |  {backup_label}")
        if is_safe:
            QMessageBox.information(self, "✅ Saved",
                f"Invoice folder set to:\n{new_dir}\n\n{backup_label} detected — your invoices will be automatically backed up!")
        else:
            QMessageBox.information(self, "Saved — Remember to Back Up!",
                f"Invoice folder set to:\n{new_dir}\n\n⚠️ This folder is not cloud-synced. Please ensure you back up regularly.")

    def change_db_location(self):
        new_dir = QFileDialog.getExistingDirectory(self, "Select Folder to Store Database", os.path.expanduser("~"))
        if not new_dir:
            return
            
        new_path = os.path.join(new_dir, "billing.db")
        old_path = config_manager.get_db_path()
        
        if new_path == old_path:
            return

        is_safe, backup_label = self._check_backup_safety(new_dir)
        if not is_safe:
            reply = QMessageBox.warning(
                self, "⚠️ Backup Risk — Please Read Carefully",
                "<b>The folder you selected does not appear to be backed up to the cloud.</b><br><br>"
                "Your database contains ALL your client records, invoices, and payment history. "
                "If your computer is lost or damaged, you will lose everything permanently.<br><br>"
                "<b>We strongly recommend choosing a folder inside:</b><br>"
                "• Google Drive<br>• OneDrive<br>• Dropbox<br>• iCloud Drive<br><br>"
                "Are you sure you want to use this local folder? <b>You accept full responsibility "
                "for backing up your data.</b>",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
            
        if QMessageBox.question(self, "Relocate Data", 
                                f"Move your database to:\n{new_path}?\n\nThis will transfer all your current records.",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                if os.path.exists(old_path):
                    if not os.path.exists(new_dir):
                        os.makedirs(new_dir)
                    shutil.copy2(old_path, new_path)
                
                config_manager.set_db_path(new_path)
                self.db_path_lbl.setText(f"Current Database Path: {new_path}  |  {backup_label}")
                self.update_sync_status()
                
                if is_safe:
                    QMessageBox.information(self, "✅ Success",
                        f"Database relocated!\n\n{backup_label} detected — your data will be automatically backed up.")
                else:
                    QMessageBox.information(self, "Moved — Remember to Back Up!",
                        "Database relocated.\n\n⚠️ This folder is not cloud-synced. Please back up billing.db regularly.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to relocate database: {e}")


    def create_input_group(self, parent_layout, label_text, placeholder, is_row=False):
        group = QVBoxLayout() if not is_row else QVBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet("font-weight: bold; color: #34495e; font-size: 12px;")
        
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        line_edit.setMinimumHeight(35)
        line_edit.setMaximumHeight(35)
        line_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdde1;
                border-radius: 5px;
                padding: 0 10px;
                background-color: #fcfcfc;
            }
            QLineEdit:focus { border: 1px solid #3498DB; background-color: #fff; }
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

    def save_office(self):
        firm_name = self.firm_name_input.text().strip()
        address = self.address_input.text().strip()
        gstin = self.gstin_input.text().strip()
        pan = self.pan_input.text().strip()
        email = self.email_input.text().strip()
        decl = self.declaration_input.toPlainText().strip()
        invoice_format = self.invoice_format_input.text().strip() or "A4CA/{FY}/{MM}/{SEQ}"
        
        initial_serial = 0
        if self.initial_serial_input.text().strip().isdigit():
            initial_serial = int(self.initial_serial_input.text().strip())
        
        if not firm_name or not address or not gstin or not pan:
            QMessageBox.warning(self, "Validation", "Firm Name, Address, GSTIN, and PAN are required.")
            return

        conn = self.db.get_connection()
        try:
            if self.current_id:
                conn.execute("""
                    UPDATE offices 
                    SET firm_name=?, address=?, gstin=?, pan=?, email=?, declaration=?, invoice_format=?, initial_serial=?
                    WHERE id=?
                """, (firm_name, address, gstin, pan, email, decl, invoice_format, initial_serial, self.current_id))
                QMessageBox.information(self, "Success", "Business profile updated.")
            else:
                conn.execute("""
                    INSERT INTO offices (firm_name, address, gstin, pan, email, declaration, invoice_format, initial_serial, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (firm_name, address, gstin, pan, email, decl, invoice_format, initial_serial))
                QMessageBox.information(self, "Success", "Business profile saved.")
                
            conn.commit()
            self.clear_form()
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        finally:
            conn.close()

    def enable_scheduler(self):
        confirm = QMessageBox.question(self, "Enable Scheduler", "Schedule daily backups/emails at 8:00 PM?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.No: return
        
        try:
            script_path = os.path.abspath(os.path.join(os.getcwd(), "main.py"))
            python_exe = sys.executable
            if platform.system() == "Windows":
                 # Use triple quotes for Windows command to handle spaces in paths
                 cmd = f'schtasks /create /tn "CABillingDailyTask" /tr "\\"{python_exe}\\" \\"{script_path}\\" --daily-task" /sc daily /st 20:00 /f'
                 subprocess.run(cmd, shell=True, check=True)
            else:
                 cron_job = f'0 20 * * * cd {os.getcwd()} && "{python_exe}" "{script_path}" --daily-task'
                 try:
                     current_cron = subprocess.check_output("crontab -l", shell=True, text=True)
                 except:
                     current_cron = ""
                 if cron_job not in current_cron:
                     new_cron = current_cron + cron_job + "\n"
                     process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
                     process.communicate(input=new_cron.encode())
            QMessageBox.information(self, "Success", "Daily task scheduled.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def load_data(self):
        while self.card_layout.count() > 1:
            item = self.card_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        conn = self.db.get_connection()
        try:
            rows = conn.execute("SELECT * FROM offices WHERE is_active = 1").fetchall()
            for row in rows:
                card = self.create_office_card(row)
                self.card_layout.insertWidget(self.card_layout.count() - 1, card)
        finally:
            conn.close()

    def create_office_card(self, row):
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet("background-color: #fff; border: 1px solid #eee; border-radius: 8px; padding: 12px;")
        layout = QHBoxLayout(card)
        
        text_layout = QVBoxLayout()
        name_lbl = QLabel(f"<b>{row['firm_name']}</b>")
        name_lbl.setStyleSheet("font-size: 14px; color: #2c3e50;")
        addr_lbl = QLabel(row['address'])
        addr_lbl.setWordWrap(True)
        addr_lbl.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        
        text_layout.addWidget(name_lbl)
        text_layout.addWidget(addr_lbl)
        layout.addLayout(text_layout, 5)
        
        btn_layout = QHBoxLayout()
        edit_btn = QPushButton("Edit")
        edit_btn.setFixedWidth(60)
        edit_btn.setStyleSheet("background-color: #f39c12; color: white; border-radius: 4px; padding: 4px;")
        edit_btn.clicked.connect(lambda: self.load_for_editing(row))
        
        del_btn = QPushButton("Del")
        del_btn.setFixedWidth(60)
        del_btn.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 4px; padding: 4px;")
        del_btn.clicked.connect(lambda: self.delete_office(row['id']))
        
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(del_btn)
        layout.addLayout(btn_layout, 1)
        return card

    def update_preview(self):
        import datetime
        now = datetime.datetime.now()
        
        year = now.year
        month = now.month
        if month >= 4:
            fy = f"{str(year)[-2:]}{str(year + 1)[-2:]}"
        else:
            fy = f"{str(year - 1)[-2:]}{str(year)[-2:]}"
            
        month_str = now.strftime("%m")
        
        format_text = self.invoice_format_input.text() or "A4CA/{FY}/{MM}/{SEQ}"
        
        initial_serial = 0
        if self.initial_serial_input.text().strip().isdigit():
            initial_serial = int(self.initial_serial_input.text().strip())
        
        # If they start at 14, the next generated is 15. If 0, next is 1.
        preview_serial = initial_serial + 1 if initial_serial >= 0 else 1
        seq_str = f"{preview_serial:03d}"
        
        preview_text = format_text.replace('{FY}', fy).replace('{MM}', month_str).replace('{SEQ}', seq_str)
        self.preview_label.setText(f"Preview: {preview_text}")

    def load_for_editing(self, row):
        r = dict(row)
        self.current_id = r['id']
        self.firm_name_input.setText(r['firm_name'])
        self.address_input.setText(r['address'])
        self.gstin_input.setText(r['gstin'])
        self.pan_input.setText(r['pan'])
        self.email_input.setText(r['email'] or '')
        self.invoice_format_input.setText(r.get('invoice_format') or "A4CA/{FY}/{MM}/{SEQ}")
        self.initial_serial_input.setText(str(r.get('initial_serial', 0)))
        self.update_preview()
        self.declaration_input.setPlainText(r['declaration'] or DEFAULT_DECLARATION)
        self.save_btn.setText("Update Business Profile")
        self.save_btn.setStyleSheet("background-color: #E67E22; color: white; font-weight: bold; height: 45px; border-radius: 6px;")

    def delete_office(self, office_id):
        if QMessageBox.question(self, "Delete", "Archive this profile?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            conn = self.db.get_connection()
            try:
                conn.execute("UPDATE offices SET is_active=0 WHERE id=?", (office_id,))
                conn.commit()
                self.load_data()
                if self.current_id == office_id: self.clear_form()
            finally: conn.close()

    def clear_form(self):
        self.current_id = None
        self.firm_name_input.clear()
        self.address_input.clear()
        self.gstin_input.clear()
        self.pan_input.clear()
        self.email_input.clear()
        self.invoice_format_input.setText("A4CA/{FY}/{MM}/{SEQ}")
        self.initial_serial_input.setText("0")
        self.update_preview()
        self.declaration_input.setPlainText(DEFAULT_DECLARATION)
        self.save_btn.setText("Save Business Profile")
        self.save_btn.setStyleSheet("background-color: #3498DB; color: white; font-weight: bold; height: 45px; border-radius: 6px;")
