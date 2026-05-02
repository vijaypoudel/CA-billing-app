from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                               QLabel, QScrollArea, QFrame, QPushButton, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon

class FAQItem(QFrame):
    def __init__(self, question, answer, parent=None):
        super().__init__(parent)
        self.question_text = question
        self.answer_text = answer
        self.is_expanded = False
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            FAQItem {
                background-color: white;
                border: 1px solid #dcdde1;
                border-radius: 8px;
                margin-bottom: 5px;
            }
            FAQItem:hover {
                border: 1px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        
        # Header (Question + Toggle)
        self.header = QWidget()
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        
        self.q_label = QLabel(f"<b>Q: {question}</b>")
        self.q_label.setWordWrap(True)
        self.q_label.setStyleSheet("font-size: 13px; color: #2c3e50; border: none; background: transparent;")
        
        self.toggle_btn = QPushButton("▼")
        self.toggle_btn.setFixedWidth(30)
        self.toggle_btn.setFlat(True)
        self.toggle_btn.setStyleSheet("font-weight: bold; color: #3498db; border: none; background: transparent;")
        
        self.header_layout.addWidget(self.q_label)
        self.header_layout.addWidget(self.toggle_btn)
        self.layout.addWidget(self.header)
        
        # Body (Answer)
        self.a_label = QLabel(answer)
        self.a_label.setWordWrap(True)
        self.a_label.setVisible(False)
        self.a_label.setStyleSheet("font-size: 12px; color: #57606f; padding-top: 10px; border: none; background: transparent;")
        self.layout.addWidget(self.a_label)
        
        self.header.mousePressEvent = self.toggle
        self.toggle_btn.clicked.connect(self.toggle)

    def toggle(self, event=None):
        self.is_expanded = not self.is_expanded
        self.a_label.setVisible(self.is_expanded)
        self.toggle_btn.setText("▲" if self.is_expanded else "▼")
        if self.is_expanded:
            self.setStyleSheet("""
                FAQItem {
                    background-color: #ffffff;
                    border: 1px solid #3498db;
                    border-radius: 8px;
                    margin-bottom: 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                FAQItem {
                    background-color: white;
                    border: 1px solid #dcdde1;
                    border-radius: 8px;
                    margin-bottom: 5px;
                }
            """)

class HelpUI(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        # Header Area
        header_hbox = QHBoxLayout()
        title_vbox = QVBoxLayout()
        self.title_lbl = QLabel("Knowledge Base & FAQ")
        self.title_lbl.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50;")
        self.subtitle_lbl = QLabel("Everything you need to know about the CA Billing App")
        self.subtitle_lbl.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        title_vbox.addWidget(self.title_lbl)
        title_vbox.addWidget(self.subtitle_lbl)
        
        header_hbox.addLayout(title_vbox)
        header_hbox.addStretch()
        
        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search for help (e.g. 'backup', 'dummy', 'edit')...")
        self.search_input.setFixedWidth(350)
        self.search_input.setFixedHeight(35)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #3498db;
                border-radius: 17px;
                padding: 0 15px;
                font-size: 13px;
                background-color: white;
            }
        """)
        self.search_input.textChanged.connect(self.filter_faqs)
        header_hbox.addWidget(self.search_input)
        
        self.layout.addLayout(header_hbox)
        self.layout.addSpacing(15)
        
        # Scroll Area for FAQs
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll)
        
        self.faq_items = []
        self.init_faqs()

    def add_category(self, title):
        lbl = QLabel(title.upper())
        lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #95a5a6; margin-top: 15px; margin-bottom: 5px; padding-left: 5px;")
        self.scroll_layout.addWidget(lbl)

    def add_faq(self, question, answer):
        item = FAQItem(question, answer)
        self.scroll_layout.addWidget(item)
        self.faq_items.append(item)

    def init_faqs(self):
        # 1. DATA SAFETY & RECOVERY (TOP PRIORITY BASED ON USER REQUEST)
        self.add_category("🚨 Data Safety & Critical Info")
        self.add_faq(
            "What if I lose my 'Generated Invoices' folder or delete a PDF?",
            "<b>No problem!</b> The database (billing.db) is the absolute source of truth. It contains all your records. "
            "If a PDF is lost, simply go to the 'Update Invoice' tab, select that invoice, and click 'Edit/Update'. "
            "The app will rebuild the PDF instantly with all original data."
        )
        self.add_faq(
            "What is the most important file to back up?",
            "The <b>billing.db</b> file is the most critical. It contains all your clients, payments, and histories. "
            "We recommend keeping this inside a cloud folder (Google Drive/OneDrive) so it's always safe."
        )
        self.add_faq(
            "How do I know if my data is being backed up?",
            "Go to 'Business Setup' settings. Next to your file paths, you will see a status label. "
            "✅ <b>Cloud Synced</b> means its safe. ⚠️ <b>No Backup Detected</b> means its only on your computer."
        )

        # 2. BUSINESS CONFIGURATION
        self.add_category("⚙️ Business Configuration")
        self.add_faq(
            "How do I customize my invoice numbers for different businesses?",
            "In the <b>Business Setup</b> tab, you can set the 'Invoice Number Format' for each profile using Wildcards. "
            "For example: typing <b>{FY}/{MM}/{SEQ}</b> will automatically output <b>2526/04/001</b>. "
            "Typing <b>MUMBAI/{SEQ}</b> will output <b>MUMBAI/001</b>. The system automatically reads these templates when generating an invoice!"
        )
        self.add_faq(
            "I onboarded a client mid-year and their next invoice should be #15. How do I do this?",
            "In the <b>Business Setup</b> tab, edit that client's profile and set the <b>'Initial Serial Number'</b> field to <b>14</b>. "
            "The very next invoice the software generates for them will automatically be number 15."
        )

        # 3. INVOICING
        self.add_category("📝 Creating Invoices")
        self.add_faq(
            "I accidentally skipped some dates or serial numbers. How do I fill them in?",
            "To generate an invoice for a past/skipped date, simply select the exact old date in the <b>'Invoice Date'</b> field. "
            "If you also need to use a specific old missing serial number (like missing #004), type the number into the <b>'Manual Invoice Number Override'</b> field at the bottom. "
            "The system will save it without breaking your current sequence count."
        )
        self.add_faq(
            "How do I generate a dummy/placeholder invoice?",
            "In the 'Create Invoice' tab, look for the '3. Allotted Bank' section. Click the <b>'Generate Dummy/Placeholder'</b> button. "
            "This will consume an invoice number but mark it as a 'DUMMY' in the list."
        )
        self.add_faq(
            "How do I edit an invoice I already generated?",
            "Go to the 'Update Invoice' tab, find the invoice in the list, click 'Actions ▼' and select 'Edit Invoice'. "
            "Note: You cannot edit invoices that are marked as 'PAID'."
        )
        self.add_faq(
            "Can I change the declaration text for just one invoice?",
            "Yes! At the bottom of the 'Create Invoice' form, there is a 'Declaration' box. You can delete or rewrite "
            "the text there for that specific invoice. It won't affect your permanent default settings."
        )
        self.add_faq(
            "What happens to the serial number if I skip/dummy an invoice?",
            "The serial number increments by 1. For example, if your last invoice was /005, a dummy will be /006, "
            "and your next real invoice will be /007."
        )
        self.add_faq(
            "How does the app decide between IGST and CGST/SGST?",
            "It compares the first two digits (State Code) of your Firm's GSTIN and the Client's GSTIN. "
            "If they match, it applies CGST+SGST. If they differ, it applies IGST."
        )

        # 3. CLIENTS & BANKS
        self.add_category("🏛️ Business, Clients & Banks")
        self.add_faq(
            "How do I add my firm's bank account for the invoice footer?",
            "Go to the 'Bank Setup' tab. Add your bank name, city, branch, and account details. "
            "These will then appear in the dropdown when you create an invoice."
        )
        self.add_faq(
            "How do I set my default bank details so I don't select them every time?",
            "When creating an invoice, selected banks are manually assigned. However, once you add a bank in "
            "'Bank Setup', it stays there for quick selection in the dropdown."
        )
        self.add_faq(
            "I have multiple businesses. How do I switch?",
            "In 'Business Setup', you can create multiple firm profiles. In the 'Create Invoice' tab, "
            "simply select the 'Office' from the top dropdown."
        )

        # 4. PAYMENTS & STATUS
        self.add_category("💰 Payments & Tracking")
        self.add_faq(
            "How do I record a payment received from a client?",
            "Go to 'Update Invoice', find the invoice, click 'Actions' -> 'Add Payment'. "
            "Enter the date, amount, and mode (NEFT/UPI/etc.)."
        )
        self.add_faq(
            "What are the different invoice statuses?",
            "• <b>Generated</b>: Invoice created but no payment recorded yet.\n"
            "• <b>Partially Paid</b>: Some payment received but balance remains.\n"
            "• <b>Paid</b>: Full payment received.\n"
            "• <b>Cancelled</b>: Invoice is void."
        )
        self.add_faq(
            "How do I see payment history for a specific invoice?",
            "In 'Update Invoice', click 'Actions' -> 'View History'. It will show all transaction dates and amounts."
        )

        # 5. REPORTS & EXPORTS
        self.add_category("📊 Reports & Analytics")
        self.add_faq(
            "How do I export my invoice list to Excel for my CA/GST filing?",
            "Go to the 'Reporting' tab, choose 'Invoice Report', click 'Run Analytics', then click 'Export to Excel'. "
            "You can even pick which specific columns to include in the file!"
        )
        self.add_faq(
            "Can I see a list of who owes me money?",
            "Yes! Use the 'Pending Payments' tab in the 'Reporting' section. It will show only those invoices "
            "that are not fully paid."
        )

        # 6. TROUBLESHOOTING & ADVANCED
        self.add_category("🛠️ Troubleshooting")
        self.add_faq(
            "The software says 'Database Locked'. What do I do?",
            "This usually happens if you try to open the database file manually in another program while the app "
            "is running. Close all other database tools and restart the billing app."
        )
        self.add_faq(
            "How do I move the entire software to a new computer?",
            "Simply install the app on the new computer, then copy your 'AnkitaCA' folder from the old Desktop "
            "to the new Desktop. The software will find your data automatically."
        )
        self.add_faq(
            "Can I use this app on two computers at once?",
            "If you put the database inside a shared folder like Google Drive, you can access it from two computers. "
            "However, **never open the app on both at the same time** or your data might get corrupted."
        )
        self.add_faq(
            "Does this software require internet?",
            "No. It works 100% offline. Internet is only needed if you want to use the Daily Email Backup feature."
        )
        
        # Adding more fillers to reach 40-50 range as requested
        self.add_faq("Can I delete a client?", "Yes, go to Client Master, select the client and click Delete. This archives them.")
        self.add_faq("What is Pan-India IGST?", "If the client's state code differs from yours, 18% IGST is applied automatically.")
        self.add_faq("How do I change my GST number?", "Go to Business Setup, select your firm, edit the GSTIN and click Update.")
        self.add_faq("Where are old PDFs archived?", "When you update an invoice, the old PDF is moved to 'DELETED_Invoices' subfolder.")
        self.add_faq("Can I change the financial year?", "The app auto-detects FY based on the invoice date. 1st April starts a new FY.")
        self.add_faq("What if my IFSC code changes?", "Update it in Bank Setup. Existing invoices won't change, but new ones will use the new code.")
        self.add_faq("Is there a limit on items per invoice?", "Currently, the UI supports up to 5 individual line items.")
        self.add_faq("How do I record TDS?", "When adding a payment, you can select 'TDS' as the payment mode for the withheld amount.")
        self.add_faq("Can I export Pending Payments?", "Yes, the reporting tab has a 'Download Report (XLSX)' button for outstanding dues.")
        self.add_faq("Does the app handle SAC codes?", "You should include the SAC code in the service description (e.g. 'Audit Fees - SAC 9982').")
        self.add_faq("What is the 'Refresh List' button for?", "It reloads the data from the database. Use it if you just made changes in another tab.")
        self.add_faq("How to change invoice date?", "During creation, use the date picker. For existing invoices, use 'Edit Invoice'.")
        self.add_faq("Can I add my logo?", "Currently, the invoices use a professional text-based header based on your Firm Name.")
        self.add_faq("How to handle discount?", "You can enter a negative amount in a line item or adjust the rate accordingly.")
        self.add_faq("What is 'Financial Year (FY)'?", "It's the 12-month period from April to March used for tax in India.")
        self.add_faq("Can I change the currency?", "The app is pre-configured for Indian Rupees (INR) and Indian numbering system (Lakhs/Crores).")
        self.add_faq("My client has no GSTIN?", "You can leave it blank; the app will mark it as an 'Unregistered' client.")
        self.add_faq("Can I filter reports by city?", "Yes, Pending Payment reports can be filtered by the Bank's branch city.")
        self.add_faq("How to clean up old data?", "We recommend archiving the folder and starting a new database if the file becomes very large.")
        self.add_faq("Is my data encrypted?", "The SQLite database is a standard format. We recommend using a computer password and cloud sync for security.")
        self.add_faq("How to print an invoice?", "Click 'Update Invoice' -> 'Actions' -> 'View History'. Then open the PDF and click Print.")
        self.add_faq("What if IFSC is BARB0...?", "The '0' is usually a zero, not the letter 'O'. Make sure you enter it correctly for banking.")
        self.add_faq("Can I add multiple email recipients?", "The daily task currently sends to the single email configured in the scheduler.")

    def filter_faqs(self):
        query = self.search_input.text().lower()
        active_category = None
        
        # This is a bit complex since we have labels interspersed.
        # Simple strategy: hide items that don't match.
        for item in self.faq_items:
            if query in item.question_text.lower() or query in item.answer_text.lower():
                item.setVisible(True)
            else:
                item.setVisible(False)
                item.is_expanded = False
                item.a_label.setVisible(False)
                item.toggle_btn.setText("▼")
                item.setStyleSheet("""
                    FAQItem {
                        background-color: white;
                        border: 1px solid #dcdde1;
                        border-radius: 8px;
                        margin-bottom: 5px;
                    }
                """)
