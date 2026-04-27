import sys
import os
import logging
import argparse
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_daily_tasks():
    try:
        from daily_tasks import main as daily_main
        daily_main()
    except Exception as e:
        logging.error(f"Daily task failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="CA Billing App")
    parser.add_argument("--daily-task", action="store_true", help="Run background daily tasks (backup/email)")
    args = parser.parse_args()

    if args.daily_task:
        run_daily_tasks()
        return

    app = QApplication(sys.argv)
    app.setApplicationName("CA Billing App")
    
    # Set Global Font to avoid warnings and ensure professional look
    # Windows prefers Segoe UI, Mac prefers System
    font = QFont("Segoe UI" if os.name == "nt" else "Arial", 10)
    app.setFont(font)
    
    # --- License Check ---
    import license_manager
    is_licensed, expiry, msg = license_manager.check_license()
    
    if not is_licensed:
        from ui.license_ui import LicenseDialog
        dialog = LicenseDialog(message=msg)
        result = dialog.exec()
        if not dialog.activated:
            logging.info("License not activated. Exiting.")
            sys.exit(0)
    else:
        logging.info(f"License OK: {msg}")
    # --- End License Check ---
    
    try:
        from ui.main_window import MainWindow
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.critical(f"Application crash: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import signal
    # Allow Ctrl+C to kill the app
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
