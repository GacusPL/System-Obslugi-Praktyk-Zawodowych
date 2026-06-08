from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from app.pdf.base import NumberedCanvas, get_premium_styles

def generate_zal_nr4b(filepath, data):
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
        
    story.append(Paragraph("ZAŁĄCZNIK NR 4B", styles['Subtitle']))
    story.append(Paragraph("WNIOSEK O ZALICZENIE PRAKTYKI NA PODSTAWIE DOŚWIADCZENIA ZAWODOWEGO", styles['Title']))
    story.append(Spacer(1, 10))
    
    # Student Metadata
    meta_data = [
        [Paragraph("Student:", styles['Label']), Paragraph(data.get('student_name', ''), styles['Body']),
         Paragraph("Nr Albumu:", styles['Label']), Paragraph(data.get('nr_albumu', ''), styles['Body'])],
        [Paragraph("Kierunek:", styles['Label']), Paragraph(data.get('kierunek', ''), styles['Body']),
         Paragraph("Specjalność:", styles['Label']), Paragraph(data.get('specjalnosc', ''), styles['Body'])],
    ]
    meta_table = Table(meta_data, colWidths=[90, 150, 110, 137])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # Form of experience
    typ_map = {
        'praca_zawodowa': 'Praca zawodowa (zatrudnienie)',
        'staz': 'Staż / praktyka zewnętrzna',
        'dzialalnosc_gospodarcza': 'Prowadzenie własnej działalności gospodarczej'
    }
    typ_text = typ_map.get(data.get('typ', ''), data.get('typ', ''))
    story.append(Paragraph(f"<b>Wnioskowana forma zaliczenia:</b> {typ_text}", styles['Body']))
    story.append(Spacer(1, 10))
    
    # Justification
    story.append(Paragraph("<b>Uzasadnienie wniosku:</b>", styles['Label']))
    story.append(Paragraph(data.get('uzasadnienie', 'Brak uzasadnienia.'), styles['Body']))
    story.append(Spacer(1, 15))
    
    # Attachments
    story.append(Paragraph("<b>Załączone dokumenty:</b>", styles['Label']))
    zalaczniki = data.get('zalaczniki', [])
    if zalaczniki:
        for idx, z in enumerate(zalaczniki):
            story.append(Paragraph(f"{idx+1}. {z}", styles['Body']))
    else:
        story.append(Paragraph("Brak załączników.", styles['Body']))
    story.append(Spacer(1, 20))
    
    # Commission opinion
    story.append(Paragraph("Opinia Komisji Dydaktycznej:", styles['H2']))
    story.append(Paragraph(data.get('opinia_komisji', 'Oczekuje na opinię komisji.'), styles['Body']))
    story.append(Spacer(1, 15))
    
    # Director decision
    decision_map = {
        'zgoda_pelna': 'Zgoda pełna na zaliczenie praktyki',
        'zgoda_czesciowa': 'Zgoda częściowa (wymagane uzupełnienie brakujących efektów)',
        'odmowa': 'Odmowa zaliczenia praktyki'
    }
    decyzja_text = decision_map.get(data.get('decyzja', ''), 'Oczekuje na decyzję Dyrektora.')
    story.append(Paragraph(f"<b>Decyzja Dyrektora Instytutu:</b> {decyzja_text}", styles['Body']))
    story.append(Spacer(1, 30))
    
    # Signatures
    sig_data = [
        [
            Paragraph("....................................................<br/>Podpis Dyrektora", styles['Body']),
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
