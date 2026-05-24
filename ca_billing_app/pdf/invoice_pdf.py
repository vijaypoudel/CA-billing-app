import os
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Frame, PageTemplate, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from utils.num_wrapper import num_to_words
from config_manager import config_manager

INVOICE_ROOT = "Invoices"

DEFAULT_DECLARATION = (
    "1. All the details mentioned in the invoice are true and correct.<br/>"
    "2. Please transfer the fee in our Account- Ankita Agarwal &amp; Associates<br/>"
    "maintained at Bank of Baroda, IFSC: BARB0DILSHA Account No.<br/>"
    "31680200002026."
)

class InvoicePDFGenerator:
    def __init__(self):
        self.invoice_path = None

    def generate(self, invoice_data, declaration_text=None):
        inv = invoice_data['invoice']
        client = invoice_data['client']
        office = invoice_data['office']
        items = invoice_data['items']

        # Determine path
        fy = inv['financial_year']
        month = inv['month_str']
        
        # Use user-configured storage folder (default: ~/Desktop/AnkitaCA)
        storage_root = config_manager.get_storage_folder()
        dir_path = os.path.join(storage_root, "Generated Invoices", fy, month)
        
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
        style_h = ParagraphStyle('Header', parent=style_n, fontName='Helvetica-Bold', fontSize=14, alignment=1) # 1 = TA_CENTER
        style_s = ParagraphStyle('Small', parent=style_n, fontSize=8)
        
        # 1. HEADER SECTION (Firm Info + Title)
        
        style_l_bold = ParagraphStyle('LeftBold', parent=style_s, fontName='Helvetica-Bold')
        style_l_bold_firm = ParagraphStyle('LeftBoldFirm', parent=style_s, fontName='Helvetica-Bold', fontSize=10)

        # Build single table to ensure perfectly aligned heights and borders
        address_text = office.get('address', '').strip()
        clean_address = re.sub(r'(?i)^address\s*:\s*', '', address_text)
        row0 = [Paragraph(office['firm_name'].upper(), style_l_bold_firm), '', "Invoice No.", "Invoice Date"]
        row1 = [Paragraph("<b>Address:</b>", style_l_bold), Paragraph(clean_address, style_s), inv['invoice_number'], inv['invoice_date']]
        row2 = [Paragraph("<b>PAN</b>", style_l_bold), Paragraph(office['pan'], style_s), '', '']
        row3 = [Paragraph("<b>GSTIN:</b>", style_l_bold), Paragraph(office['gstin'], style_s), '', '']
        row4 = [Paragraph("<b>E-mail:</b>", style_l_bold), Paragraph(office.get('email', ''), style_s), '', '']

        header_data = [row0, row1, row2, row3, row4]
        
        # Total width = 19.5cm
        # Right side = 3.5 + 3.5 = 7.0cm
        # Left side = 19.5 - 7.0 = 12.5cm
        # Left column splits into 2.2cm for labels, 10.3cm for values
        header_table = Table(header_data, colWidths=[2.2*cm, 10.3*cm, 3.5*cm, 3.5*cm])
        
        # Determine background color based on image (light grey)
        bg_color = colors.HexColor('#EBEBEB')
        
        header_table.setStyle(TableStyle([
            # Outer box
            ('BOX', (0,0), (-1,-1), 1, colors.black),
            # Vertical line separating left and right section
            ('LINEBEFORE', (2,0), (2,-1), 1, colors.black),
            # Vertical line between Invoice No and Invoice Date
            ('LINEBEFORE', (3,0), (3,-1), 1, colors.black),
            # Horizontal line separating headers and values on right side
            ('LINEBELOW', (2,0), (3,0), 1, colors.black),
            
            # Left box firm name spans 2 columns
            ('SPAN', (0,0), (1,0)), 
            
            # Right box values span down to match left box height
            ('SPAN', (2,1), (2,4)), 
            ('SPAN', (3,1), (3,4)), 
            
            # Background
            ('BACKGROUND', (0,0), (-1,-1), bg_color), 
            
            # Alignment
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('VALIGN', (2,1), (3,4), 'MIDDLE'), # Center right side values vertically
            ('ALIGN', (2,0), (3,-1), 'CENTER'), # Center right side text horizontally
            
            # Fonts for right side header
            ('FONTNAME', (2,0), (3,0), 'Helvetica-Bold'),
            ('FONTSIZE', (2,0), (3,0), 9),
            
            # Fonts for right side values
            ('FONTNAME', (2,1), (3,-1), 'Helvetica'),
            ('FONTSIZE', (2,1), (3,-1), 9),
            
            # Padding
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('LEFTPADDING', (0,0), (1,-1), 2), # Left padding for text labels
        ]))
        
        elements.append(Paragraph("Tax Invoice", style_h))
        elements.append(Spacer(1, 0.4*cm))
        
        # --- EXPORT DECLARATIONS ---
        if inv.get('is_export'):
            export_style = ParagraphStyle('ExportDecl', parent=style_s, alignment=1, fontName='Helvetica-Bold', fontSize=10, leading=12)
            elements.append(Paragraph("SUPPLY MEANT FOR EXPORT UNDER LUT WITHOUT PAYMENT OF IGST", export_style))
            
            lut_arn = office.get('lut_arn', '')
            lut_expiry = office.get('lut_expiry', '')
            if lut_arn:
                lut_text = f"LUT ARN: {lut_arn}"
                if lut_expiry:
                    lut_text += f" ({lut_expiry})"
                elements.append(Paragraph(lut_text, export_style))
            
            # Conversion Rate if present
            conv_rate = inv.get('conversion_rate')
            conv_date = inv.get('conversion_date')
            if conv_rate:
                note = f"Conversion Rate: {conv_rate}"
                if conv_date:
                    note += f" (as on {conv_date})"
                elements.append(Paragraph(f"<i>Note: {note}</i>", ParagraphStyle('Note', parent=style_s, alignment=1, fontSize=9)))
            
            elements.append(Spacer(1, 0.4*cm))

        elements.append(header_table)
        
        # Box around top section - removed space to attach to Bill To
        elements.append(Spacer(1, 0))

        # 2. BILL TO SECTION
        # Extract POS from client address if possible, else placeholder
        pos = inv.get('place_of_supply', '') # Placeholder based on image, normally derived from Client State
        
        # Handle Unregistered/International Clients - Hide GSTIN line if unregistered
        display_gstin = client['gstin']
        bill_data = [
            [Paragraph("<b>Bill To:</b>", style_n)],
<<<<<<< Updated upstream
            [Paragraph(client['client_name'].upper(), style_b)],
            [Paragraph(client['address'] or "", style_s)],
            [Paragraph(f"<b>GSTIN: {display_gstin}</b>", style_b)],
            [Paragraph(f"<b>POS:</b> &nbsp;&nbsp;&nbsp;{pos}", style_s)]
=======
            [Paragraph(client['client_name'].upper(), style_n)],
            [Paragraph(client['address'] or "", style_n)]
>>>>>>> Stashed changes
        ]
        
        if display_gstin and not display_gstin.startswith('URP-'):
            bill_data.append([Paragraph(f"<b>GSTIN: {display_gstin}</b>", style_n)])
        else:
            # If international/unregistered, maybe just show "International / Unregistered" if user wants, 
            # but user said "remove gstin", so we skip the label entirely.
            pass
            
        bill_data.append([Paragraph(f"<b>POS:</b> &nbsp;&nbsp;&nbsp;{pos}", style_n)])
        
        bill_table = Table(bill_data, colWidths=[19.5*cm])
        bill_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.black),
            ('LINEABOVE', (0,-1), (0,-1), 1, colors.black), # Line above POS (last row)
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,-1), (0,-1), 4), # Extra padding for POS
            ('BOTTOMPADDING', (0,-1), (0,-1), 4),
        ]))
        elements.append(bill_table)
        elements.append(Spacer(1, 0))
        
        # 3. ITEMS TABLE
        # Columns: S.No, Desc, HSN, Taxable, CGST(Rate, Amt), SGST(Rate, Amt), IGST(Rate, Amt)
        
        # Header Row 1
        # S.No | Desc | HSN | Taxable | CGST | SGST | IGST
        #                               Rate|Amt|Rate|Amt|Rate|Amt
        
        # To do merged cells in ReportLab, we define row 0 and row 1
        
        currency = "INR" # India-specific branch: Always INR
        curr_map = {'USD': '($)', 'EUR': '(€)', 'GBP': '(£)', 'INR': '(INR)'}
        sym = '(INR)'
        
        h1 = ['S. No.', 'Description of Services', 'HSN', f'Taxable Value {sym}'.strip(), 'CGST', '', 'SGST', '', 'IGST', '']
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
        
        # Column Widths (Sum to exactly 19.5cm for A4 max space)
        # S.No(1.0), Desc(8.5), HSN(1.0), Taxable Value(2.5) => Total 13.0cm
        # GST Section: 0.8 (Rate) + 1.4 (Amt) x 3 = 6.6cm
        # 13.0 + 6.6 = 19.6? Wait. 
        # 1.0 + 8.2 + 1.0 + 2.5 + 0.8 + 1.4 + 0.8 + 1.4 + 0.8 + 1.6 = 19.5
        cw = [1.0*cm, 8.2*cm, 1.0*cm, 2.5*cm,  0.8*cm, 1.4*cm,  0.8*cm, 1.4*cm,  0.8*cm, 1.6*cm]
        
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
            ('ALIGN', (1,-1), (1,-1), 'RIGHT'), # 'Total' label right align in col 1
            
            # Right align financial columns from row 2 (data) down to the total row
            ('ALIGN', (3,2), (3,-1), 'RIGHT'), # Taxable Value
            ('ALIGN', (5,2), (5,-1), 'RIGHT'), # CGST Amount
            ('ALIGN', (7,2), (7,-1), 'RIGHT'), # SGST Amount
            ('ALIGN', (9,2), (9,-1), 'RIGHT'), # IGST Amount
            
            # Add a slight right padding so they don't touch the border
            ('RIGHTPADDING', (3,2), (3,-1), 4),
            ('RIGHTPADDING', (5,2), (5,-1), 4),
            ('RIGHTPADDING', (7,2), (7,-1), 4),
            ('RIGHTPADDING', (9,2), (9,-1), 4),
        ]))
        elements.append(t)
        
        # 4. TOTALS & WORDS
        grand_total = inv['grand_total']
        grand_total_rounded = round(grand_total) # Assuming rounding
        
        # Total Box
        elements.append(Spacer(1, 0)) # No space, attach to table
        
        is_export_conv = inv.get('is_export') and inv.get('conversion_rate')
        
        tot_data = [
            [Paragraph("<i>Total Invoice Value (In figures)</i>", style_s), f"{sym.strip('()')} {grand_total_rounded:,.2f}"]
        ]
        
        # Add original currency words ONLY if not doing an export conversion
        if not is_export_conv:
            tot_data.append([
                Paragraph("<i>Total Invoice Value (In words)</i>", style_s), 
                Paragraph(num_to_words(grand_total_rounded, currency=currency), ParagraphStyle('CenterBold', parent=style_s, alignment=1, fontName='Helvetica-Bold'))
            ])
        
        # Add INR conversion row if applicable
        if is_export_conv:
            try:
                rate = float(inv['conversion_rate'])
                inr_total = grand_total * rate
                inr_total_rounded = round(inr_total)
                
                tot_data.append([
                    Paragraph("<b>Final Total in INR (Converted)</b>", style_s), 
                    f"INR {inr_total_rounded:,.2f}"
                ])
                # Add Words for INR as the FINAL word line
                tot_data.append([
                    Paragraph("<i>Total INR Value (In words)</i>", style_s),
                    Paragraph(num_to_words(inr_total_rounded, currency='INR'), ParagraphStyle('CenterBold', parent=style_s, alignment=1, fontName='Helvetica-Bold'))
                ])
            except Exception as e:
                print(f"Conversion error in PDF: {e}")
                
        # Align this table with main divisions: Col 0+1+2+3 = 1.0 + 7.0 + 1.5 + 3.5 = 13.0cm
        tot_table = Table(tot_data, colWidths=[13.0*cm, 6.5*cm])
        tot_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'), # Values are bold
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'), # Center align both labels and values
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (0,-1), 10), # Add some padding from left border for the labels
        ]))
        elements.append(tot_table)
        
        # Reverse Charge
        elements.append(Spacer(1, 0)) # attach to table
        rc_data = [[Paragraph("<i>Whether tax is payable on reverse charge basis:</i>", style_s), Paragraph("<i>No</i>", style_s)]]
        rc_table = Table(rc_data, colWidths=[13.0*cm, 6.5*cm])
        rc_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'), # Left align labels
            ('LEFTPADDING', (0,0), (-1,-1), 10), # Add some padding from left border
        ]))
        elements.append(rc_table)
        
        # 5. FOOTER (Declaration & Bank)
        elements.append(Spacer(1, 0)) # attach to table
        
        # Declaration: use per-invoice override → office saved → hardcoded default
        if declaration_text and declaration_text.strip():
            decl_body = declaration_text.strip().replace('\n', '<br/>')
        elif office.get('declaration') and office['declaration'].strip():
            decl_body = office['declaration'].strip().replace('\n', '<br/>')
        else:
            decl_body = DEFAULT_DECLARATION
        bank_details = f"<b>Declaration:</b><br/>{decl_body}"
        
        # Signature
        style_c_small = ParagraphStyle('CenterSmall', parent=style_s, alignment=1) # 1=TA_CENTER
        firm_name_p = Paragraph(f"<b>{office['firm_name']}</b>", style_c_small)
        
        # Check if signature image exists
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sig_image_path = os.path.join(base_dir, 'assets', 'signature.png')
        
        if os.path.exists(sig_image_path):
            sig_img = Image(sig_image_path, width=4*cm, height=1.5*cm)
            sig_p = [Spacer(1, 0.2*cm), sig_img, Paragraph("Valid Signature<br/>(Authorised Signatory)", style_c_small)]
        else:
            sig_p = Paragraph("<br/>"*4 + "Valid Signature<br/>(Authorised Signatory)", style_c_small)
        
        footer_data = [
            [Paragraph(bank_details, style_s), firm_name_p],
            ['', sig_p]
        ]
        
        footer_table = Table(footer_data, colWidths=[13.0*cm, 6.5*cm])
        footer_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.black),
            ('LINEBEFORE', (1,0), (1,-1), 1, colors.black),
            ('SPAN', (0,0), (0,1)),
            ('VALIGN', (0,0), (0,1), 'TOP'),
            ('VALIGN', (1,0), (1,0), 'TOP'),
            ('VALIGN', (1,1), (1,1), 'BOTTOM'),
            ('ALIGN', (1,0), (1,1), 'CENTER'),
            ('TOPPADDING', (1,0), (1,0), 6),
            ('BOTTOMPADDING', (1,1), (1,1), 6),
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
             
             # LEFTPADDING of Tables is 6 by default. So we indent the Paragraph to perfectly align in a straight line.
             padded_footer_style = ParagraphStyle('FooterPadded', parent=style_s, fontName='Helvetica-Oblique', leftIndent=6)
             elements.append(Paragraph(footer_text, padded_footer_style))

        doc.build(elements)
        return self.invoice_path
