from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from app.pdf.base import NumberedCanvas, get_premium_styles

def generate_zal_nr5(filepath, data):
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
        
    story.append(Paragraph("ZAŁĄCZNIK NR 5", styles['Subtitle']))
    story.append(Paragraph("ANONIMOWA ANKIETA EVALUACYJNA PRAKTYKI ZAWODOWEJ", styles['Title']))
    story.append(Spacer(1, 10))
    
    # Metryczka (Anonymous)
    meta_data = [
        [Paragraph("Kierunek:", styles['Label']), Paragraph(data.get('kierunek', ''), styles['Body']),
         Paragraph("Semestr:", styles['Label']), Paragraph(str(data.get('semestr', '')), styles['Body'])],
        [Paragraph("Forma studiów:", styles['Label']), Paragraph(data.get('forma_studiow', ''), styles['Body']),
         Paragraph("Liczba godzin:", styles['Label']), Paragraph(f"{data.get('godziny', '960')} godz.", styles['Body'])],
        [Paragraph("Rok Akademicki:", styles['Label']), Paragraph(data.get('rok_akademicki', ''), styles['Body']),
         "", ""]
    ]
    meta_table = Table(meta_data, colWidths=[110, 140, 90, 147])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('SPAN', (0, 2), (1, 2)),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # Questions & Answers Table
    story.append(Paragraph("Odpowiedzi na pytania ankietowe (skala 1-5):", styles['H2']))
    
    ank_headers = [
        Paragraph("Nr", styles['TableHeader']),
        Paragraph("Treść pytania ewaluacyjnego", styles['TableHeader']),
        Paragraph("Ocena", styles['TableHeader'])
    ]
    ank_data = [ank_headers]
    
    odpowiedzi = data.get('odpowiedzi', [])
    # 14 standard evaluation questions
    questions = [
        "Jasność sformułowania celów praktyki",
        "Zgodność realizowanych prac z programem praktyki",
        "Współpraca z opiekunem zakładowym (ZOPZ)",
        "Współpraca z opiekunem uczelnianym (UOPZ)",
        "Przygotowanie merytoryczne studenta do zadań",
        "Organizacja stanowiska pracy w zakładzie",
        "Możliwość korzystania z narzędzi/oprogramowania",
        "Atmosfera w zespole i zakładzie pracy",
        "Pomoc udzielana przez pracowników firmy",
        "Możliwość rozwoju kompetencji miękkich",
        "Ocena przydatności praktyki w przyszłej karierze",
        "Wskazanie słabych punktów i trudności",
        "Ocena ułatwień techniczno-organizacyjnych uczelni",
        "Ogólne zadowolenie z odbytej praktyki"
    ]
    
    for idx, q_text in enumerate(questions):
        # find answer for question_nr = idx + 1
        score = "-"
        for ans in odpowiedzi:
            if ans.get('pytanie_nr') == idx + 1:
                score = str(ans.get('odpowiedz', '-'))
                break
        
        ank_data.append([
            Paragraph(str(idx + 1), styles['TableBody']),
            Paragraph(q_text, styles['TableBody']),
            Paragraph(score, styles['TableBody'])
        ])
        
    ank_table = Table(ank_data, colWidths=[40, 390, 57])
    ank_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(ank_table)
    story.append(Spacer(1, 15))
    
    # Remarks
    story.append(Paragraph(f"<b>Uwagi i wnioski studenta:</b><br/>{data.get('uwagi', 'Brak uwag.')}", styles['Body']))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("<font color='#64748b' size='8'><i>Niniejsza ankieta została wypełniona drogą elektroniczną i jest w pełni anonimowa. Nie zawiera danych pozwalających na identyfikację autora.</i></font>", styles['Body']))
    
    doc.build(story, canvasmaker=NumberedCanvas)
