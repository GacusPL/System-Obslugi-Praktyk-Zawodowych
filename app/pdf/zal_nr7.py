from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from app.pdf.base import get_premium_styles, PageNumberCanvas


def _esc(text):
    """Escapuje znaki specjalne, zachowując łamanie wierszy jako <br/>."""
    text = (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return text.replace('\n', '<br/>')


def generate_zal_nr7(filepath, data):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=64,
        leftMargin=64,
        topMargin=48,
        bottomMargin=54,
        title="Załącznik nr 7 - Sprawozdanie z praktyki zawodowej"
    )

    styles = get_premium_styles()
    italic_font = 'Arial-Italic' if 'Arial-Italic' in pdfmetrics.getRegisteredFontNames() else 'Arial'

    # Style wierne wzorcowi docx
    zal_no = ParagraphStyle('Zal7No', parent=styles['Body'], fontSize=10, leading=13,
                            alignment=2, textColor=colors.black)  # prawy górny róg
    header_inst = ParagraphStyle('Zal7Header', parent=styles['Body'], fontName='Arial-Bold',
                                 fontSize=11, leading=15, alignment=0, textColor=colors.black)
    doc_title = ParagraphStyle('Zal7Title', parent=styles['Title'], fontSize=14, leading=18,
                               alignment=1, spaceBefore=6, spaceAfter=2, textColor=colors.black)
    title_sub = ParagraphStyle('Zal7TitleSub', parent=styles['Body'], fontSize=11, leading=15,
                               alignment=1, textColor=colors.black, spaceAfter=4)
    meta = ParagraphStyle('Zal7Meta', parent=styles['Body'], fontSize=11, leading=20, textColor=colors.black)
    section_head = ParagraphStyle('Zal7Section', parent=styles['Body'], fontName='Arial-Bold',
                                  fontSize=11, leading=15, alignment=0, spaceBefore=14, spaceAfter=2,
                                  textColor=colors.black)
    section_inst = ParagraphStyle('Zal7Inst', parent=styles['Body'], fontName=italic_font,
                                  fontSize=9.5, leading=13, alignment=0, textColor=colors.HexColor("#555555"),
                                  spaceAfter=6)
    content = ParagraphStyle('Zal7Content', parent=styles['Body'], fontSize=10.5, leading=15,
                             alignment=4, textColor=colors.black)  # justify
    sign = ParagraphStyle('Zal7Sign', parent=styles['Body'], fontSize=10.5, leading=14,
                          alignment=1, textColor=colors.black)

    story = []

    # Numer załącznika - prawy górny róg
    story.append(Paragraph("Załącznik nr 7", zal_no))
    story.append(Spacer(1, 6))

    # Nagłówek instytucjonalny (pogrubiony, do lewej)
    story.append(Paragraph("Akademia Nauk Stosowanych w Elblągu", header_inst))
    story.append(Paragraph("Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego", header_inst))
    story.append(Spacer(1, 18))

    # Metryczka studenta (większy odstęp między nazwiskiem a nr albumu)
    studia = data.get('forma_studiow') or ''
    studia_txt = f"inżynierskie {studia}".strip() if studia else "inżynierskie"
    album_row = Table(
        [[Paragraph(f"Student: <b>{_esc(data.get('student_name', ''))}</b>", meta),
          Paragraph(f"Nr albumu: <b>{_esc(data.get('nr_albumu', ''))}</b>", meta)]],
        colWidths=[300, 167]
    )
    album_row.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(album_row)
    story.append(Paragraph(f"Kierunek: <b>{_esc(data.get('kierunek', 'informatyka'))}</b>", meta))
    story.append(Paragraph(f"Specjalność: <b>{_esc(data.get('specjalnosc', '') or '—')}</b>", meta))
    story.append(Paragraph(f"Studia: <b>{_esc(studia_txt)}</b>", meta))
    story.append(Paragraph(f"Rok ak.: <b>{_esc(data.get('rok_akademicki', ''))}</b>", meta))
    story.append(Spacer(1, 16))

    # Tytuł
    story.append(Paragraph("SPRAWOZDANIE STUDENTA<br/>Z PRAKTYKI ZAWODOWEJ", doc_title))
    story.append(Paragraph(f"odbytej w {_esc(data.get('zaklad_nazwa', ''))}", title_sub))
    story.append(Spacer(1, 10))

    # Sekcje wg wzorca: numer rzymski + tytuł (bold, do lewej) + kursywa instrukcji + treść
    sekcje = [
        ("I. CHARAKTERYSTYKA MIEJSCA ODBYWANIA PRAKTYKI",
         "(Krótki opis instytucji, w której odbywała się praktyka zawodowa)",
         data.get('sekcja_I', '')),
        ("II. OPIS I ANALIZA WYKONYWANYCH PRAC",
         "(Syntetyczny opis wykonanych prac)",
         data.get('sekcja_II', '')),
        ("III. WIEDZA I UMIEJĘTNOŚCI UZYSKANE W TRAKCIE PRAKTYKI",
         "(Samoocena w zakresie nabytych kompetencji oraz osiągniętych efektów uczenia się)",
         data.get('sekcja_III', '')),
    ]
    for tytul, instrukcja, tresc in sekcje:
        story.append(Paragraph(tytul, section_head))
        story.append(Paragraph(instrukcja, section_inst))
        # Treść wypełniana przez studenta (z systemu) - pogrubiona dla odróżnienia od szablonu
        story.append(Paragraph(f"<b>{_esc(tresc)}</b>", content))

    story.append(Spacer(1, 36))

    # Podpis (prawa strona, wg wzorca)
    sign_table = Table(
        [[Paragraph("…………………………………………<br/>data i podpis studenta", sign)]],
        colWidths=[230]
    )
    sign_table.hAlign = 'RIGHT'
    sign_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(sign_table)

    doc.build(story, canvasmaker=PageNumberCanvas)
