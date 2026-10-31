import io
from datetime import date
from decimal import Decimal
from app.models.invoice import Invoice


def generate_invoice_pdf(invoice: Invoice) -> bytes:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        elements = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'InvoiceSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=15
        )
        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1e293b')
        )
        bold_style = ParagraphStyle(
            'BodyBold',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#0f172a')
        )

        # Header
        elements.append(Paragraph("<b>BRIGHTLOOP SOFTWARE</b>", title_style))
        elements.append(Paragraph("Subscription Management & Cloud Solutions<br/>Email: billing@brightloop.com | Web: www.brightloop.com", subtitle_style))
        elements.append(Spacer(1, 10))

        # Metadata Table
        customer_name = invoice.customer.user.full_name if invoice.customer and invoice.customer.user else "Valued Customer"
        company = invoice.customer.company_name if invoice.customer and invoice.customer.company_name else ""
        address = invoice.customer.address or ""
        gst = invoice.customer.gst_number or "N/A"

        meta_data = [
            [
                Paragraph(f"<b>Billed To:</b><br/>{customer_name}<br/>{company}<br/>{address}<br/>GST: {gst}", body_style),
                Paragraph(
                    f"<b>Invoice #:</b> {invoice.invoice_number}<br/>"
                    f"<b>Date:</b> {invoice.invoice_date.strftime('%Y-%m-%d')}<br/>"
                    f"<b>Due Date:</b> {invoice.due_date.strftime('%Y-%m-%d')}<br/>"
                    f"<b>Status:</b> {invoice.status.value.upper()}<br/>"
                    f"<b>Period:</b> {invoice.billing_period_start or 'N/A'} to {invoice.billing_period_end or 'N/A'}",
                    body_style
                )
            ]
        ]
        meta_table = Table(meta_data, colWidths=[270, 270])
        meta_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 15))

        # Line items
        table_data = [
            [
                Paragraph("<b>Item & Description</b>", bold_style),
                Paragraph("<b>Qty</b>", bold_style),
                Paragraph("<b>Unit Price (₹)</b>", bold_style),
                Paragraph("<b>Tax (₹)</b>", bold_style),
                Paragraph("<b>Discount (₹)</b>", bold_style),
                Paragraph("<b>Total (₹)</b>", bold_style)
            ]
        ]

        for line in invoice.lines:
            item_title = line.product.name if line.product else "Service"
            if line.variant:
                item_title += f" ({line.variant.variant_name})"
            if line.description:
                item_title += f"<br/><font size=8 color='#64748b'>{line.description}</font>"

            table_data.append([
                Paragraph(item_title, body_style),
                Paragraph(str(line.quantity), body_style),
                Paragraph(f"{line.unit_price:.2f}", body_style),
                Paragraph(f"{line.tax_amount:.2f}", body_style),
                Paragraph(f"{line.discount_amount:.2f}", body_style),
                Paragraph(f"{line.line_total:.2f}", body_style)
            ])

        line_table = Table(table_data, colWidths=[200, 40, 80, 70, 70, 80])
        line_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(line_table)
        elements.append(Spacer(1, 15))

        # Totals Summary
        summary_data = [
            ["Subtotal:", f"₹ {invoice.subtotal:.2f}"],
            ["Tax Amount:", f"₹ {invoice.tax_amount:.2f}"],
            ["Discount Amount:", f"- ₹ {invoice.discount_amount:.2f}"],
            ["Grand Total:", f"₹ {invoice.total:.2f}"],
            ["Amount Paid:", f"₹ {invoice.amount_paid:.2f}"],
            ["Balance Due:", f"₹ {invoice.amount_due:.2f}"],
        ]
        summary_table = Table(summary_data, colWidths=[400, 140])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 3), (1, 3), 'Helvetica-Bold'),
            ('FONTNAME', (0, 5), (1, 5), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 5), (1, 5), colors.HexColor('#dc2626') if invoice.amount_due > 0 else colors.HexColor('#16a34a')),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(summary_table)

        # Notes
        if invoice.notes:
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("<b>Notes / Terms:</b>", bold_style))
            elements.append(Paragraph(invoice.notes, body_style))

        elements.append(Spacer(1, 30))
        elements.append(Paragraph("<font size=8 color='#94a3b8'>Thank you for subscribing to Brightloop Software. This is a computer-generated invoice.</font>", body_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        # Fallback text format if reportlab is not available
        content = f"""
============================================================
              BRIGHTLOOP SOFTWARE - INVOICE
============================================================
Invoice Number: {invoice.invoice_number}
Date: {invoice.invoice_date}
Due Date: {invoice.due_date}
Status: {invoice.status.value.upper()}
Customer: {invoice.customer.user.full_name if invoice.customer and invoice.customer.user else 'N/A'}
Subtotal: Rs. {invoice.subtotal}
Tax: Rs. {invoice.tax_amount}
Discount: Rs. {invoice.discount_amount}
Grand Total: Rs. {invoice.total}
Paid: Rs. {invoice.amount_paid}
Due: Rs. {invoice.amount_due}
============================================================
"""
        return content.encode("utf-8")
