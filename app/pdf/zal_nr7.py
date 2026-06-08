from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from app.pdf.base import NumberedCanvas, get_premium_styles

def generate_zal_nr7(filepath, data):
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
        
    story.append(Paragraph("ZAŁĄCZNIK NR 7", styles['Subtitle']))
    story.append(Paragraph("SPRAWOZDANIE STUDENTA Z PRAKTYKI ZAWODOWEJ", styles['Title']))
    story.append(Spacer(1, 10))
    
    # Student Metadata
    meta_data = [
        [Paragraph("Student:", styles['Label']), Paragraph(data.get('student_name', ''), styles['Body']),
         Paragraph("Nr Albumu:", styles['Label']), Paragraph(data.get('nr_albumu', ''), styles['Body'])],
        [Paragraph("Kierunek:", styles['Label']), Paragraph(data.get('kierunek', ''), styles['Body']),
         Paragraph("Specjalność:", styles['Label']), Paragraph(data.get('specjalnosc', ''), styles['Body'])],
        [Paragraph("Miejsce praktyki:", styles['Label']), Paragraph(data.get('zaklad_nazwa', ''), styles['Body']),
         Paragraph("Rok Akademicki:", styles['Label']), Paragraph(data.get('rok_akademicki', ''), styles['Body'])],
    ]
    meta_table = Table(meta_data, colWidths=[90, 150, 110, 137])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # Section I
    story.append(Paragraph("Sekcja I: Opis struktury organizacyjnej zakładu pracy", styles['H1']))
    story.append(Paragraph(data.get('sekcja_I', '').replace('\n', '<br/>'), styles['Body']))
    story.append(Spacer(1, 15))
    
    # Section II
    story.append(Paragraph("Sekcja II: Opis stanowisk pracy i realizowanych zadań", styles['H1']))
    story.append(Paragraph(data.get('sekcja_II', '').replace('\n', '<br/>'), styles['Body']))
    story.append(Spacer(1, 15))
    
    # Section III
    story.append(Paragraph("Sekcja III: Podsumowanie, wnioski i ocena własna studenta", styles['H1']))
    story.append(Paragraph(data.get('sekcja_III', '').replace('\n', '<br/>'), styles['Body']))
    story.append(Spacer(1, 30))
    
    # Signature
    sig_data = [
        [
            "",
            Paragraph("....................................................<br/>Podpis Studenta", styles['Body'])
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
