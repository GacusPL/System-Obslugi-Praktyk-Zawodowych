from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from app.pdf.base import NumberedCanvas, get_premium_styles

def generate_zal_nr3(filepath, data):
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
        
    story.append(Paragraph("ZAŁĄCZNIK NR 3", styles['Subtitle']))
    story.append(Paragraph("KARTA PRZEBIEGU PRAKTYKI ZAWODOWEJ", styles['Title']))
    story.append(Spacer(1, 10))
    
    # Student & Metadata
    meta_data = [
        [Paragraph("Student:", styles['Label']), Paragraph(data.get('student_name', ''), styles['Body']),
         Paragraph("Nr Albumu:", styles['Label']), Paragraph(data.get('nr_albumu', ''), styles['Body'])],
        [Paragraph("Kierunek:", styles['Label']), Paragraph(data.get('kierunek', ''), styles['Body']),
         Paragraph("Specjalność:", styles['Label']), Paragraph(data.get('specjalnosc', ''), styles['Body'])],
        [Paragraph("Zakład Pracy:", styles['Label']), Paragraph(data.get('zaklad_nazwa', ''), styles['Body']),
         Paragraph("Opiekun Uczelniany:", styles['Label']), Paragraph(data.get('uopz_name', ''), styles['Body'])],
        [Paragraph("Termin od:", styles['Label']), Paragraph(data.get('termin_od', ''), styles['Body']),
         Paragraph("Termin do:", styles['Label']), Paragraph(data.get('termin_do', ''), styles['Body'])],
    ]
    meta_table = Table(meta_data, colWidths=[90, 150, 110, 137])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # BHP training
    bhp_text = f"Szkolenie BHP i p.poż. odbyło się w dniu rozpoczęcia praktyki: <b>{'TAK' if data.get('bhp_completed', True) else 'NIE'}</b>"
    story.append(Paragraph(bhp_text, styles['Body']))
    story.append(Spacer(1, 15))
    
    # ZOPZ evaluation
    story.append(Paragraph("1. Ocena wystawiona przez Opiekuna Zakładowego (ZOPZ)", styles['H1']))
    zopz_headers = [
        Paragraph("Kryterium oceny", styles['TableHeader']),
        Paragraph("Ocena", styles['TableHeader'])
    ]
    zopz_data = [
        zopz_headers,
        [Paragraph("Systematyczność i punktualność", styles['TableBody']), Paragraph(str(data.get('ocena_zopz_1', '-')), styles['TableBody'])],
        [Paragraph("Przestrzeganie dyscypliny i przepisów BHP", styles['TableBody']), Paragraph(str(data.get('ocena_zopz_2', '-')), styles['TableBody'])],
        [Paragraph("Stosunek do współpracowników i klientów", styles['TableBody']), Paragraph(str(data.get('ocena_zopz_3', '-')), styles['TableBody'])],
        [Paragraph("Przydatność zawodowa i zaangażowanie", styles['TableBody']), Paragraph(str(data.get('ocena_zopz_4', '-')), styles['TableBody'])],
        [Paragraph("Efektywność i jakość wykonywanej pracy", styles['TableBody']), Paragraph(str(data.get('ocena_zopz_5', '-')), styles['TableBody'])],
        [Paragraph("<b>OCENA OGÓLNA PRAKTYKANTA:</b>", styles['Label']), Paragraph(f"<b>{data.get('ocena_zopz_ogolna', '-')}</b>", styles['Label'])]
    ]
    zopz_table = Table(zopz_data, colWidths=[380, 107])
    zopz_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f8fafc")),
    ]))
    story.append(zopz_table)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(f"<b>Opinia opisowa ZOPZ:</b><br/>{data.get('opinia_zopz_opis', 'Brak opinii opisowej.')}", styles['Body']))
    story.append(Spacer(1, 15))
    
    # UOPZ evaluation
    story.append(Paragraph("2. Weryfikacja i ocena Opiekuna Uczelnianego (UOPZ)", styles['H1']))
    story.append(Paragraph(f"<b>Opinia opisowa UOPZ:</b><br/>{data.get('opinia_uopz_opis', 'Brak opinii opisowej.')}", styles['Body']))
    story.append(Spacer(1, 10))
    
    uopz_headers = [
        Paragraph("Kryterium oceny", styles['TableHeader']),
        Paragraph("Ocena", styles['TableHeader'])
    ]
    uopz_data = [
        uopz_headers,
        [Paragraph("Ocena za sprawozdanie końcowe", styles['TableBody']), Paragraph(str(data.get('ocena_sprawozdania', '-')), styles['TableBody'])],
        [Paragraph("<b>OCENA KOŃCOWA Z PRAKTYKI:</b>", styles['Label']), Paragraph(f"<b>{data.get('ocena_koncowa', '-')}</b>", styles['Label'])]
    ]
    uopz_table = Table(uopz_data, colWidths=[380, 107])
    uopz_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0d9488")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#f8fafc")),
    ]))
    story.append(uopz_table)
    story.append(Spacer(1, 25))
    
    # Signatures
    sig_data = [
        [
            Paragraph("....................................................<br/>Podpis ZOPZ", styles['Body']),
            Paragraph("....................................................<br/>Podpis UOPZ", styles['Body'])
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
