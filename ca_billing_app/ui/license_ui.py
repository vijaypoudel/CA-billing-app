"""
License activation dialog shown when the app has no valid license.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import license_manager


class LicenseDialog(QDialog):
    """
    A modal dialog that blocks the entire application until the user
    enters a valid license key.  Pressing 'X' or Cancel quits the app.
    """

    def __init__(self, message: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("CA Billing App — License Activation")
        self.setFixedSize(520, 340)
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint
        )
        self.activated = False
        self._build_ui(message)

    def _build_ui(self, message: str):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(30, 24, 30, 24)

        # Title
        title = QLabel("License Activation Required")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Message
        if message:
            msg_label = QLabel(message)
            msg_label.setWordWrap(True)
            msg_label.setStyleSheet("color: #c0392b; font-size: 12px;")
            msg_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(msg_label)

        # Instructions
        info = QLabel(
            "Please enter the license key provided by your software vendor.\n"
            "If you don't have a key, contact your vendor for assistance."
        )
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #555; font-size: 11px;")
        layout.addWidget(info)

        # Key input
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Paste your license key here…")
        self.key_input.setMinimumHeight(36)
        self.key_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        layout.addWidget(self.key_input)

        # Buttons
        btn_layout = QHBoxLayout()

        self.activate_btn = QPushButton("Activate")
        self.activate_btn.setMinimumHeight(36)
        self.activate_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
                padding: 6px 24px;
            }
            QPushButton:hover { background-color: #2ecc71; }
            QPushButton:pressed { background-color: #1e8449; }
        """)
        self.activate_btn.clicked.connect(self._on_activate)

        self.quit_btn = QPushButton("Quit")
        self.quit_btn.setMinimumHeight(36)
        self.quit_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
                padding: 6px 24px;
            }
            QPushButton:hover { background-color: #ec7063; }
            QPushButton:pressed { background-color: #c0392b; }
        """)
        self.quit_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.activate_btn)
        btn_layout.addWidget(self.quit_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Status label (shows result after activation attempt)
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

    def _on_activate(self):
        key = self.key_input.text().strip()
        if not key:
            self.status_label.setText("Please enter a license key.")
            self.status_label.setStyleSheet("color: #e67e22; font-size: 11px;")
            return

        is_valid, expiry, msg = license_manager.validate_key(key)

        if is_valid:
            license_manager.save_license(key)
            self.status_label.setText(f"✅ {msg}")
            self.status_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 12px;")
            self.activated = True

            QMessageBox.information(
                self, "License Activated",
                f"Your license has been activated successfully!\n\n{msg}"
            )
            self.accept()
        else:
            self.status_label.setText(f"❌ {msg}")
            self.status_label.setStyleSheet("color: #c0392b; font-weight: bold; font-size: 12px;")

    def reject(self):
        """Overridden: pressing X or Quit means exit the entire app."""
        super().reject()
