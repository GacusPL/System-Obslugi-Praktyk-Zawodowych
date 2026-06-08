from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from app.pdf.base import NumberedCanvas, get_premium_styles

def generate_zal_nr6(filepath, data):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=40, # smaller margins for wide table
        leftMargin=40,
        topMargin=54,
        bottomMargin=72
    )
    
    styles = get_premium_styles()
    story = []
    
    # Title
    story.append(Paragraph("ZAŁĄCZNIK NR 6", styles['Subtitle']))
    story.append(Paragraph("DZIENNIK PRZEBIEGU PRAKTYKI ZAWODOWEJ", styles['Title']))
    story.append(Spacer(1, 10))
    
    # Student & Metadata
    meta_data = [
        [Paragraph("Student:", styles['Label']), Paragraph(data.get('student_name', ''), styles['Body']),
         Paragraph("Nr Albumu:", styles['Label']), Paragraph(data.get('nr_albumu', ''), styles['Body'])],
        [Paragraph("Kierunek:", styles['Label']), Paragraph(data.get('kierunek', ''), styles['Body']),
         Paragraph("Specjalność:", styles['Label']), Paragraph(data.get('specjalnosc', ''), styles['Body'])],
        [Paragraph("Miejsce praktyki:", styles['Label']), Paragraph(data.get('zaklad_nazwa', ''), styles['Body']),
         Paragraph("Przedział czasu:", styles['Label']), Paragraph(f"{data.get('termin_od', '')} - {data.get('termin_do', '')}", styles['Body'])]
    ]
    meta_table = Table(meta_data, colWidths=[90, 160, 110, 155])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # 120 Days Table
    headers = [
        Paragraph("Dzień", styles['TableHeader']),
        Paragraph("Data", styles['TableHeader']),
        Paragraph("Opis wykonywanych prac i zadań", styles['TableHeader']),
        Paragraph("Efekty", styles['TableHeader']),
        Paragraph("Podpis ZOPZ", styles['TableHeader'])
    ]
    
    table_data = [headers]
    
    wpisy = data.get('wpisy', [])
    # Sort entries by day number
    wpisy = sorted(wpisy, key=lambda w: w.get('dzien_nr', 0))
    
    for w in wpisy:
        # Format learning effects list: e.g. "EU01, EU03"
        efekty_list = w.get('efekty', [])
        efekty_str = ", ".join([f"EU{e:02d}" for e in efekty_list]) if efekty_list else "-"
        
        podpis_status = "Zatwierdził" if w.get('status') == 'Approved' else "Brak podpisu"
        
        table_data.append([
            Paragraph(f"Dzień {w.get('dzien_nr')}", styles['TableBody']),
            Paragraph(w.get('data_wpisu', ''), styles['TableBody']),
            Paragraph(w.get('opis_prac', ''), styles['TableBody']),
            Paragraph(efekty_str, styles['TableBody']),
            Paragraph(podpis_status, styles['TableBody'])
        ])
        
    # Table column widths: total 515 pt printable area with 40pt margins
    # A4 width is 595.27pt. Margins are 40 + 40 = 80. Remaining = 515.27.
    # col widths: 50, 65, 260, 70, 70
    table = Table(table_data, colWidths=[50, 65, 260, 70, 70], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    
    story.append(table)
    
    doc.build(story, canvasmaker=NumberedCanvas)
