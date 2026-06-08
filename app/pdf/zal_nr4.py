from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from app.pdf.base import NumberedCanvas, get_premium_styles

def generate_zal_nr4(filepath, data):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=72
    )
    
    styles = get_premium_styles()
    story = []
    
    # Header Logo
    logo_path = "app/static/img/logo-ans-poziom.png"
    import os
    if os.path.exists(logo_path):
        from reportlab.platypus import Image
        img = Image(logo_path, width=120, height=35)
        header_table = Table([[img, ""]], colWidths=[150, 330])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 15))
        
    story.append(Paragraph("ZAŁĄCZNIK NR 4", styles['Subtitle']))
    story.append(Paragraph("KARTA POTWIERDZENIA EFEKTÓW UCZENIA SIĘ", styles['Title']))
    story.append(Spacer(1, 10))
    
    # Student Metadata
    meta_data = [
        [Paragraph("Student:", styles['Label']), Paragraph(data.get('student_name', ''), styles['Body']),
         Paragraph("Nr Albumu:", styles['Label']), Paragraph(data.get('nr_albumu', ''), styles['Body'])],
        [Paragraph("Kierunek:", styles['Label']), Paragraph(data.get('kierunek', ''), styles['Body']),
         Paragraph("Zrealizowane godziny:", styles['Label']), Paragraph(f"{data.get('godziny_zrealizowane', '960')} godz.", styles['Body'])],
    ]
    meta_table = Table(meta_data, colWidths=[90, 150, 130, 117])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # Effects Table
    story.append(Paragraph("Potwierdzenie osiągnięcia efektów uczenia się:", styles['H2']))
    
    eff_headers = [
        Paragraph("Nr", styles['TableHeader']),
        Paragraph("Opis efektu uczenia się", styles['TableHeader']),
        Paragraph("Uzyskano", styles['TableHeader'])
    ]
    eff_data = [eff_headers]
    
    efekty = data.get('efekty', [])
    for eff in efekty:
        uzyskano_text = "TAK" if eff.get('uzyskano') else "NIE"
        eff_data.append([
            Paragraph(f"EU{eff.get('nr', 0):02d}", styles['TableBody']),
            Paragraph(eff.get('opis', ''), styles['TableBody']),
            Paragraph(uzyskano_text, styles['TableBody'])
        ])
        
    eff_table = Table(eff_data, colWidths=[50, 370, 67])
    eff_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(eff_table)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph(f"<b>Opinia UOPZ o efektach:</b><br/>{data.get('opinia_uopz', 'Brak opinii.')}", styles['Body']))
    story.append(Spacer(1, 20))
    
    # Signatures
    sig_data = [
        [
            Paragraph("....................................................<br/>Podpis ZOPZ (Opiekun z zakładu)", styles['Body']),
            Paragraph("....................................................<br/>Podpis UOPZ (Opiekun z uczelni)", styles['Body'])
        ]
    ]
    sig_table = Table(sig_data, colWidths=[240, 247])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(sig_table)
    
    doc.build(story, canvasmaker=NumberedCanvas)
