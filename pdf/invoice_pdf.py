import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from utils.num_wrapper import num_to_words

INVOICE_ROOT = "Invoices"

class InvoicePDFGenerator:
    def __init__(self):
        self.invoice_path = None

    def generate(self, invoice_data):
        inv = invoice_data['invoice']
        client = invoice_data['client']
        office = invoice_data['office']
        items = invoice_data['items']

        # Determine path
        fy = inv['financial_year']
        month = inv['month_str']
        
        # New Desktop Path Structure: ~/Desktop/AnkitaCA/Generated Invoices/{FY}/{Month}/
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        dir_path = os.path.join(desktop, "AnkitaCA", "Generated Invoices", fy, month)
        
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
        filename = inv['invoice_number'].replace("/", "_") + ".pdf"
        self.invoice_path = os.path.join(dir_path, filename)
        
        # Document Setup
        doc = SimpleDocTemplate(self.invoice_path, pagesize=A4, 
                                rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
        
        elements = []
        styles = getSampleStyleSheet()
        style_n = styles['Normal']
        style_b = ParagraphStyle('Bold', parent=style_n, fontName='Helvetica-Bold', fontSize=9)
        style_h = ParagraphStyle('Header', parent=style_n, fontName='Helvetica-Bold', fontSize=14, alignment=TA_RIGHT)
        style_s = ParagraphStyle('Small', parent=style_n, fontSize=8)
        
        # 1. HEADER SECTION (Firm Info + Title)
        
        # Left Side: Firm Details
        address_line = f"Address: {office['address']}"
        email_line = f"E-mail: {office.get('email', '')}"
        
        firm_info = [
            [Paragraph(office['firm_name'].upper(), style_b)],
            [Paragraph(address_line, style_s)],
            [Paragraph(f"PAN : {office['pan']}", style_s)],
            [Paragraph(f"GSTIN : {office['gstin']}", style_s)],
            [Paragraph(email_line, style_s)]
        ]
        
        # Right Side: Invoice Details
        inv_details = [
            ["Invoice No.", "Invoice Date"],
            [inv['invoice_number'], inv['invoice_date']]
        ]
        
        # Combined Header Table
        # We need a table that contains the Left Info and the Right Table
        
        # Create the right-side sub-table
        right_table = Table(inv_details, colWidths=[3.5*cm, 3.5*cm])
        right_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
        
        # Main Header Grid
        header_data = [
            [Table(firm_info, colWidths=[10*cm]), right_table]
        ]
        
        header_table = Table(header_data, colWidths=[11*cm, 7*cm])
        header_table.setStyle(TableStyle([
            # ('GRID', (0,0), (-1,-1), 1, colors.black), # Outer grid if needed
             ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        
        elements.append(Paragraph("Tax Invoice", style_h))
        elements.append(Spacer(1, 0.2*cm))
        elements.append(header_table)
        
        # Box around top section
        elements.append(Spacer(1, 0.2*cm))

        # 2. BILL TO SECTION
        # Extract POS from client address if possible, else placeholder
        pos = inv.get('place_of_supply', '') # Placeholder based on image, normally derived from Client State
        
        bill_data = [
            [Paragraph("<b>Bill To:</b>", style_n)],
            [Paragraph(client['client_name'].upper(), style_b)],
            [Paragraph(client['address'] or "", style_s)],
            [Paragraph(f"<b>GSTIN: {client['gstin']}</b>", style_s)],
            [Paragraph(f"<b>POS:</b> {pos}", style_s)]
        ]
        
        bill_table = Table(bill_data, colWidths=[18*cm])
        bill_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.black),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        elements.append(bill_table)
        elements.append(Spacer(1, 0.2*cm))
        
        # 3. ITEMS TABLE
        # Columns: S.No, Desc, HSN, Taxable, CGST(Rate, Amt), SGST(Rate, Amt), IGST(Rate, Amt)
        
        # Header Row 1
        # S.No | Desc | HSN | Taxable | CGST | SGST | IGST
        #                               Rate|Amt|Rate|Amt|Rate|Amt
        
        # To do merged cells in ReportLab, we define row 0 and row 1
        
        h1 = ['S. No.', 'Description of Services', 'HSN', 'Taxable Value', 'CGST', '', 'SGST', '', 'IGST', '']
        h2 = ['', '', '', '', 'Rate', 'Amount', 'Rate', 'Amount', 'Rate', 'Amount']
        
        # Prepare Rows
        rows = [h1, h2]
        
        idx = 1
        total_taxable = 0.0
        total_cgst = 0.0
        total_sgst = 0.0
        total_igst = 0.0
        
        for item in items:
            amt = float(item['amount'])
            rate = float(item['gst_rate'])
            
            # Tax Logic
            cgst_r, cgst_a = 0, 0
            sgst_r, sgst_a = 0, 0
            igst_r, igst_a = 0, 0
            
            tax_val = amt * (rate / 100.0)
            
            if inv['tax_type'] == 'IGST':
                igst_r = rate
                igst_a = tax_val
            elif inv['tax_type'] == 'CGST_SGST':
                cgst_r = rate / 2
                cgst_a = tax_val / 2
                sgst_r = rate / 2
                sgst_a = tax_val / 2
            
            total_taxable += amt
            total_cgst += cgst_a
            total_sgst += sgst_a
            total_igst += igst_a
            
            row = [
                str(idx),
                Paragraph(item['description'], style_s),
                item['hsn_code'] or '',
                f"{amt:,.2f}",
                f"{cgst_r:g}%" if cgst_r else "0", f"{cgst_a:,.2f}" if cgst_a else "-",
                f"{sgst_r:g}%" if sgst_r else "0", f"{sgst_a:,.2f}" if sgst_a else "-",
                f"{igst_r:g}%" if igst_r else "0", f"{igst_a:,.2f}" if igst_a else "-"
            ]
            rows.append(row)
            idx += 1
            
        # Total Row
        total_row = [
            '', 'Total', '', f"{total_taxable:,.2f}", 
            '', f"{total_cgst:,.2f}" if total_cgst else "-",
            '', f"{total_sgst:,.2f}" if total_sgst else "-",
            '', f"{total_igst:,.2f}" if total_igst else "-"
        ]
        rows.append(total_row)
        
        # Column Widths
        # Total width approx 18-19cm
        cw = [1*cm, 6*cm, 1.5*cm, 2.5*cm,  1.2*cm, 1.8*cm,  1.2*cm, 1.8*cm,  1.2*cm, 1.8*cm]
        
        t = Table(rows, colWidths=cw)
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (0,1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            
            # Merges for Header
            ('SPAN', (0,0), (0,1)), # S.No
            ('SPAN', (1,0), (1,1)), # Desc
            ('SPAN', (2,0), (2,1)), # HSN
            ('SPAN', (3,0), (3,1)), # Taxable
            ('SPAN', (4,0), (5,0)), # CGST Header
            ('SPAN', (6,0), (7,0)), # SGST Header
            ('SPAN', (8,0), (9,0)), # IGST Header
            
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), # Total Row Bold
            ('SPAN', (0,-1), (0,-1)), # Total Label Span? Actually Col 1 is 'Total', Col 0 empty
        ]))
        elements.append(t)
        
        # 4. TOTALS & WORDS
        grand_total = inv['grand_total']
        grand_total_rounded = round(grand_total) # Assuming rounding
        
        # Total Box
        elements.append(Spacer(1, 0)) # No space, attach to table
        
        tot_data = [
            ["Total Invoice Value (In figures)", f"{grand_total_rounded}"],
            ["Total Invoice Value (In words)", num_to_words(grand_total_rounded)]
        ]
        tot_table = Table(tot_data, colWidths=[9*cm, 9*cm])
        tot_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), # Header/Figures bold
            ('FontSize', (0,0), (-1,-1), 9),
            ('ALIGN', (1,0), (1,0), 'RIGHT'), # Figures right align
            ('ALIGN', (1,1), (1,1), 'LEFT'), # Words left align
            ('FONTNAME', (0,1), (-1,1), 'Helvetica'), # Words row NOT bold
            ('FONTSIZE', (0,1), (-1,1), 8), # Smaller font for words to prevent overflow
        ]))
        elements.append(tot_table)
        
        # Reverse Charge
        rc_data = [["Whether tax is payable on reverse charge basis:", "No"]]
        rc_table = Table(rc_data, colWidths=[9*cm, 9*cm])
        rc_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (0,0), colors.lightblue),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('FONTNAME', (0,0), (0,0), 'Helvetica-Oblique'),
        ]))
        elements.append(rc_table)
        
        # 5. FOOTER (Declaration & Bank)
        elements.append(Spacer(1, 0.2*cm))
        
        # Bank Details - Hardcoded from image/requirements or placeholders
        bank_details = """
        <b>Declaration:</b><br/>
        1. All the details mentioned in the invoice are true and correct.<br/>
        2. Please transfer the fee in our Account- Ankita Agarwal & Associates<br/>
        maintained at Bank of Baroda, IFSC: BARB0DILSHA Account No.<br/>
        31680200002026.
        """
        
        # Signature
        sign_details = f"""
        <b>{office['firm_name']}</b><br/><br/><br/>
        Valid Signature<br/>
        (Authorised Signatory)
        """
        
        footer_data = [
            [Paragraph(bank_details, style_s), Paragraph(sign_details, style_s)]
        ]
        
        footer_table = Table(footer_data, colWidths=[10*cm, 8*cm])
        footer_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (1,0), (1,0), 'CENTER'),
        ]))
        elements.append(footer_table)
        
        # Bottom Line
        elements.append(Spacer(1, 0.1*cm))
        
        allotted_bank = inv.get('allotted_bank', '')
        allotted_branch = inv.get('allotted_branch', '')
        allotted_city = inv.get('allotted_city', '')
        
        footer_text = f"<i>Allotted by {allotted_bank}, {allotted_branch} Branch {allotted_city}</i>"
        # Fallback if empty (Only if using defaults logic, but request is: if empty, dont show)
        # The user said: "if not filled, dont have it at the footer."
        
        if allotted_bank:
             footer_text = f"<i>Allotted by {allotted_bank}, {allotted_branch} Branch {allotted_city}</i>"
             elements.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=style_s, fontName='Helvetica-Oblique')))

        doc.build(elements)
        return self.invoice_path
