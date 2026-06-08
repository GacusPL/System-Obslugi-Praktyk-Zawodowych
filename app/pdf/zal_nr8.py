from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from app.pdf.base import NumberedCanvas, get_premium_styles

def generate_zal_nr8(filepath, data):
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
        
    story.append(Paragraph("ZAŁĄCZNIK NR 8", styles['Subtitle']))
    story.append(Paragraph("PROTOKÓŁ EGZAMINU PRAKTYKI ZAWODOWEJ", styles['Title']))
    story.append(Spacer(1, 10))
    
    # Student Metadata
    meta_data = [
        [Paragraph("Student:", styles['Label']), Paragraph(data.get('student_name', ''), styles['Body']),
         Paragraph("Nr Albumu:", styles['Label']), Paragraph(data.get('nr_albumu', ''), styles['Body'])],
        [Paragraph("Kierunek:", styles['Label']), Paragraph(data.get('kierunek', ''), styles['Body']),
         Paragraph("Data egzaminu:", styles['Label']), Paragraph(data.get('data_egzaminu', ''), styles['Body'])],
    ]
    meta_table = Table(meta_data, colWidths=[90, 150, 110, 137])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # Commission skład
    story.append(Paragraph("Komisja Egzaminacyjna:", styles['H2']))
    komisja = data.get('komisja', [])
    if komisja:
        for idx, k in enumerate(komisja):
            story.append(Paragraph(f"{idx+1}. {k.get('imie')} {k.get('nazwisko')} - {k.get('rola_w_komisji')}", styles['Body']))
    else:
        story.append(Paragraph("Brak wyznaczonej komisji.", styles['Body']))
    story.append(Spacer(1, 15))
    
    # Grades summary table
    story.append(Paragraph("Zestawienie ocen cząstkowych i ocena końcowa:", styles['H2']))
    
    gr_headers = [
        Paragraph("Kryterium / Część składowa", styles['TableHeader']),
        Paragraph("Ocena", styles['TableHeader'])
    ]
    gr_data = [
        gr_headers,
        [Paragraph("Ocena opiekuna zakładowego (ZOPZ)", styles['TableBody']), Paragraph(str(data.get('ocena_zopz', '-')), styles['TableBody'])],
        [Paragraph("Ocena opiekuna uczelnianego (UOPZ)", styles['TableBody']), Paragraph(str(data.get('ocena_uopz', '-')), styles['TableBody'])],
        [Paragraph("Ocena za sprawozdanie końcowe", styles['TableBody']), Paragraph(str(data.get('ocena_sprawozdania', '-')), styles['TableBody'])],
        [Paragraph("Ocena z egzaminu ustnego", styles['TableBody']), Paragraph(str(data.get('ocena_ustna', '-')), styles['TableBody'])],
        [Paragraph("<b>OCENA KOŃCOWA Z PRAKTYKI:</b>", styles['Label']), Paragraph(f"<b>{data.get('ocena_koncowa', '-')}</b>", styles['Label'])]
    ]
    
    gr_table = Table(gr_data, colWidths=[380, 107])
    gr_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f8fafc")),
    ]))
    story.append(gr_table)
    story.append(Spacer(1, 30))
    
    # Signatures
    sig_data = [
        [
            Paragraph("....................................................<br/>Podpis Przewodniczącego Komisji", styles['Body']),
            Paragraph("....................................................<br/>Podpisy Członków Komisji", styles['Body'])
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
