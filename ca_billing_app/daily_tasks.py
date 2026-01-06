import os
import shutil
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import sys

import sys

try:
    from services.reporting_service import ReportingService
    from exports.excel_exporter import ExcelExporter
except ImportError:
    # Fallback for if we are running the script directly from inside its folder
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from services.reporting_service import ReportingService
    from exports.excel_exporter import ExcelExporter

from config_manager import config_manager

# --- CONFIGURATION ---
# USER MUST UPDATE THESE
EMAIL_SENDER = "caankita.agarwal@ymail.com" # From User Request
EMAIL_PASSWORD = "YOUR_APP_PASSWORD_HERE" # User needs to generate this
EMAIL_RECIPIENT = "caankita.agarwal@ymail.com"
SMTP_SERVER = "smtp.mail.yahoo.com" # Assuming ymail, otherwise smtp.gmail.com
SMTP_PORT = 587 # or 465 for SSL

BACKUP_DIR = os.path.join(os.path.expanduser("~"), "Desktop/AnkitaCA/Backups")
DB_PATH = config_manager.get_db_path()

def backup_database():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return None
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"billing_backup_{timestamp}.db")
    
    shutil.copy2(DB_PATH, backup_file)
    print(f"Database backed up to: {backup_file}")
    return backup_file

def generate_invoice_extract():
    # Generate Excel Report
    service = ReportingService()
    exporter = ExcelExporter()
    
    # Fetch ALL data for backup purposes
    data = service.export_data(query_type="invoices")
    
    if not data:
        print("No invoice data to extract.")
        return None
        
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Invoice_Extract_{timestamp}.xlsx"
    filepath = os.path.join(BACKUP_DIR, filename)
    
    headers = list(data[0].keys())
    exporter.export_to_excel(data, headers, filepath)
    print(f"Invoice extract created: {filepath}")
    return filepath

def send_email(attachment_path):
    if not os.path.exists(attachment_path):
        return

    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECIPIENT
    msg['Subject'] = f"Daily Invoice Extract & Backup - {datetime.date.today()}"
    
    body = "Please find attached the daily invoice extract."
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach Excel
    with open(attachment_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(attachment_path)}")
        msg.attach(part)
        
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, text)
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    print("Starting Daily Tasks...")
    backup_database()
    extract_file = generate_invoice_extract()
    if extract_file:
        # Only try to send if we have a file and credentials are mock-checked
        if EMAIL_PASSWORD != "YOUR_APP_PASSWORD_HERE":
             send_email(extract_file)
        else:
             print("Skipping email: Configuration required in daily_tasks.py")
    print("Daily Tasks Completed.")

if __name__ == "__main__":
    main()
