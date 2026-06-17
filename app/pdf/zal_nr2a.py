from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from app.pdf.base import NumberedCanvas, get_premium_styles

def generate_zal_nr2a(filepath, data):
    # Setup document
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
    
    # 1. Header with Logo (if exists)
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
        
    # Title
    story.append(Paragraph("ZAŁĄCZNIK NR 2A", styles['Subtitle']))
    story.append(Paragraph("PROGRAM I HARMONOGRAM PRAKTYKI ZAWODOWEJ", styles['Title']))
    story.append(Spacer(1, 10))
    
    # 2. Student & Practice Metadata Table
    meta_data = [
        [Paragraph("Student:", styles['Label']), Paragraph(data.get('student_name', ''), styles['Body']),
         Paragraph("Nr Albumu:", styles['Label']), Paragraph(data.get('nr_albumu', ''), styles['Body'])],
        [Paragraph("Kierunek:", styles['Label']), Paragraph(data.get('kierunek', ''), styles['Body']),
         Paragraph("Specjalność:", styles['Label']), Paragraph(data.get('specjalnosc', ''), styles['Body'])],
        [Paragraph("Zakład Pracy:", styles['Label']), Paragraph(data.get('zaklad_nazwa', ''), styles['Body']),
         Paragraph("Opiekun Uczelniany:", styles['Label']), Paragraph(data.get('uopz_name', ''), styles['Body'])],
        [Paragraph("Termin od:", styles['Label']), Paragraph(data.get('termin_od', ''), styles['Body']),
         Paragraph("Termin do:", styles['Label']), Paragraph(data.get('termin_do', ''), styles['Body'])],
        [Paragraph("Rok Akademicki:", styles['Label']), Paragraph(data.get('rok_akademicki', ''), styles['Body']),
         "", ""]
    ]
    
    meta_table = Table(meta_data, colWidths=[90, 150, 110, 137])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('SPAN', (0, 4), (1, 4)), # Span rok akademicki label + value
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))

    # 3. Program Praktyki Table (mapowanie efektów na przykładowe prace)
    program = data.get('program', [])
    if program:
        story.append(Paragraph("Program praktyki zawodowej:", styles['H2']))
        prog_headers = [
            Paragraph("Efekt kształcenia", styles['TableHeader']),
            Paragraph("Dział (komórka) / przykładowe prace praktykanta", styles['TableHeader'])
        ]
        prog_data = [prog_headers]
        for p in program:
            efekt_label = f"<b>EU{int(p.get('efekt_nr', 0)):02d}</b> – {p.get('efekt_opis', '')}"
            prog_data.append([
                Paragraph(efekt_label, styles['TableBody']),
                Paragraph(p.get('opis_realizacji') or '—', styles['TableBody'])
            ])
        prog_table = Table(prog_data, colWidths=[210, 277])
        prog_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(prog_table)
        story.append(Spacer(1, 20))

    # 4. Harmonogram Table
    story.append(Paragraph("Harmonogram Praktyki (wymagane 120 dni):", styles['H2']))
    
    harm_headers = [
        Paragraph("Lp.", styles['TableHeader']),
        Paragraph("Dział / Obszar działalności", styles['TableHeader']),
        Paragraph("Planowane dni", styles['TableHeader'])
    ]
    
    harm_data = [harm_headers]
    
    dzialy = data.get('dzialy', [])
    total_days = 0
    for idx, d in enumerate(dzialy):
        days = int(d.get('planowane_dni', 0))
        total_days += days
        harm_data.append([
            Paragraph(str(idx + 1), styles['TableBody']),
            Paragraph(d.get('nazwa_dzialu', ''), styles['TableBody']),
            Paragraph(f"{days} dni", styles['TableBody'])
        ])
        
    harm_data.append([
        "",
        Paragraph("<b>RAZEM:</b>", styles['Label']),
        Paragraph(f"<b>{total_days} dni</b>", styles['Label'])
    ])
    
    harm_table = Table(harm_data, colWidths=[40, 340, 107])
    harm_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f8fafc")),
    ]))
    story.append(harm_table)
    story.append(Spacer(1, 30))
    
    # 4. Signatures Section
    sig_data = [
        [
            Paragraph("....................................................<br/>Podpis Studenta", styles['Body']),
            Paragraph("....................................................<br/>Podpis ZOPZ (Zakładowy)", styles['Body']),
            Paragraph("....................................................<br/>Podpis UOPZ (Uczelniany)", styles['Body'])
        ],
        [
            Paragraph(f"Status: {'Złożono podpis' if data.get('podpis_student') else 'Brak podpisu'}", styles['Body']),
            Paragraph(f"Status: {'Złożono podpis' if data.get('podpis_zopz') else 'Brak podpisu'}", styles['Body']),
            Paragraph(f"Status: {'Złożono podpis' if data.get('podpis_uopz') else 'Brak podpisu'}", styles['Body'])
        ]
    ]
    
    sig_table = Table(sig_data, colWidths=[160, 160, 167])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(sig_table)
    
    # Build Document using our custom NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
