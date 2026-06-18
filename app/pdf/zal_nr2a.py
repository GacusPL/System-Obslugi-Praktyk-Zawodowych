from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from app.pdf.base import get_premium_styles, PageNumberCanvas


def _esc(text):
    text = (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return text.replace('\n', '<br/>')


def generate_zal_nr2a(filepath, data):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=48,
        bottomMargin=54,
        title="Załącznik nr 2a - Program i harmonogram praktyki zawodowej"
    )

    styles = get_premium_styles()

    zal_no = ParagraphStyle('Zal2aNo', parent=styles['Body'], fontSize=10, leading=13,
                            alignment=2, textColor=colors.black)
    header_inst = ParagraphStyle('Zal2aHeader', parent=styles['Body'], fontName='Arial-Bold',
                                 fontSize=11, leading=15, alignment=0, textColor=colors.black)
    meta = ParagraphStyle('Zal2aMeta', parent=styles['Body'], fontSize=10.5, leading=18, textColor=colors.black)
    section_head = ParagraphStyle('Zal2aSection', parent=styles['Body'], fontName='Arial-Bold',
                                  fontSize=12, leading=16, alignment=1, spaceBefore=14, spaceAfter=8,
                                  textColor=colors.black)
    th = ParagraphStyle('Zal2aTH', parent=styles['Body'], fontName='Arial-Bold', fontSize=9.5,
                        leading=12, alignment=1, textColor=colors.black)
    td = ParagraphStyle('Zal2aTD', parent=styles['Body'], fontSize=9, leading=12, textColor=colors.black)
    td_c = ParagraphStyle('Zal2aTDc', parent=td, alignment=1)
    sign = ParagraphStyle('Zal2aSign', parent=styles['Body'], fontSize=9.5, leading=13,
                          alignment=1, textColor=colors.black)

    story = []

    # Numer załącznika - prawy górny róg
    story.append(Paragraph("Załącznik nr 2a", zal_no))
    story.append(Spacer(1, 4))

    # Nagłówek instytucjonalny (pogrubiony, do lewej)
    story.append(Paragraph("Akademia Nauk Stosowanych w Elblągu", header_inst))
    story.append(Paragraph("Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego", header_inst))
    story.append(Spacer(1, 14))

    # Metryczka
    story.append(Paragraph(f"Student / ka: <b>{_esc(data.get('student_name', ''))}</b>", meta))
    story.append(Paragraph(f"Nr albumu: <b>{_esc(data.get('nr_albumu', ''))}</b>", meta))
    story.append(Paragraph(f"Kierunek studiów: <b>{_esc(data.get('kierunek', 'Informatyka'))}</b>", meta))
    story.append(Paragraph(f"Specjalność: <b>{_esc(data.get('specjalnosc', '') or '—')}</b>", meta))
    story.append(Paragraph(f"Miejsce praktyki (instytucja): <b>{_esc(data.get('zaklad_nazwa', ''))}</b>", meta))
    story.append(Paragraph(
        f"Termin realizacji praktyki: od <b>{_esc(data.get('termin_od', ''))}</b> "
        f"do <b>{_esc(data.get('termin_do', ''))}</b>"
        f"&nbsp;&nbsp;&nbsp;&nbsp;Liczba dni roboczych: <b>120</b>", meta))

    # ----- PROGRAM PRAKTYKI ZAWODOWEJ -----
    story.append(Paragraph("PROGRAM PRAKTYKI ZAWODOWEJ", section_head))

    program = data.get('program', [])
    prog_rows = [[
        Paragraph("Efekty kształcenia", th), "",
        Paragraph("Dział (komórka) / przykładowe prace wykonywane przez praktykanta", th)
    ]]
    for p in program:
        realizacja = (p.get('opis_realizacji') or '').strip()
        realizacja_html = f"<b>{_esc(realizacja)}</b>" if realizacja else ''
        prog_rows.append([
            Paragraph(f"{int(p.get('efekt_nr', 0)):02d}", td_c),
            Paragraph(_esc(p.get('efekt_opis', '')), td),
            Paragraph(realizacja_html, td)
        ])
    prog_table = Table(prog_rows, colWidths=[28, 252, 215], repeatRows=1)
    prog_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(prog_table)
    story.append(Spacer(1, 26))

    # ----- HARMONOGRAM PRAKTYKI ZAWODOWEJ -----
    story.append(Paragraph("HARMONOGRAM PRAKTYKI ZAWODOWEJ", section_head))

    dzialy = data.get('dzialy', [])
    harm_rows = [[
        Paragraph("L.p.", th),
        Paragraph("Dział / komórka<br/>(miejsce odbywania praktyki)", th),
        Paragraph("Planowana liczba<br/>dni roboczych", th)
    ]]
    total = 0
    for idx, d in enumerate(dzialy, start=1):
        dni = int(d.get('planowane_dni', 0) or 0)
        total += dni
        harm_rows.append([
            Paragraph(str(idx), td_c),
            Paragraph(f"<b>{_esc(d.get('nazwa_dzialu', ''))}</b>", td),
            Paragraph(f"<b>{dni}</b>", td_c)
        ])
    harm_rows.append([Paragraph("", td), Paragraph("<b>Łącznie</b>", td), Paragraph(f"<b>{total}</b>", td_c)])
    harm_rows.append([Paragraph("", td), Paragraph("<b>Wymagana</b>", td), Paragraph("<b>120</b>", td_c)])

    harm_table = Table(harm_rows, colWidths=[40, 350, 105], repeatRows=1)
    harm_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(harm_table)
    story.append(Spacer(1, 18))

    # Uzgodniono w dniu + podpisy (3 kolumny wg wzorca)
    story.append(Paragraph("Uzgodniono w dniu: …………………………………………", meta))
    story.append(Spacer(1, 24))

    sig_data = [[
        Paragraph("……………………………………<br/>podpis uczelnianego<br/>opiekuna praktyki", sign),
        Paragraph("……………………………………<br/>podpis zakładowego<br/>opiekuna praktyki", sign),
        Paragraph("……………………………………<br/>podpis studenta", sign),
    ]]
    sig_table = Table(sig_data, colWidths=[165, 165, 165])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(sig_table)

    doc.build(story, canvasmaker=PageNumberCanvas)
