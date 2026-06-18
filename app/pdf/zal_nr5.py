from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from app.pdf.base import PageNumberCanvas
from app.pdf._common import esc, doc_styles, header_flowables

SKALA = ["zdecydowanie\ntak", "raczej\ntak", "trudno\npowiedzieć", "raczej\nnie", "zdecydowanie\nnie"]


def generate_zal_nr5(filepath, data):
    from app.routes.api.ankieta import QUESTIONS

    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=42, leftMargin=42,
                            topMargin=48, bottomMargin=54,
                            title="Załącznik nr 5 - Kwestionariusz ankiety")
    s = doc_styles()
    story = header_flowables(s, "Załącznik nr 5")
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Kwestionariusz ankiety oceniający przebieg praktyk zawodowych realizowanych w ramach "
        "programów studiów w Instytucie Informatyki Stosowanej im. K. Brzeskiego w Elblągu", s['title']))
    story.append(Paragraph(
        "W trosce o stałe podnoszenie jakości przebiegu praktyk zawodowych zwracamy się do Pani/Pana "
        "z prośbą o wypełnienie anonimowej ankiety dotyczącej praktyk zawodowych, w której należy określić "
        "w jakim stopniu zgadza się Pan/Pani z poniższymi stwierdzeniami.", s['body']))
    story.append(Paragraph("Prosimy zaznaczyć przy każdym pytaniu X w wybranym polu odpowiedzi.", s['body']))
    story.append(Spacer(1, 8))

    # Mapa odpowiedzi: pytanie_nr -> wartość 1-5 (5 = zdecydowanie tak)
    answers = {o.get('pytanie_nr'): o.get('odpowiedz') for o in data.get('odpowiedzi', [])}

    header = [Paragraph("", s['th'])] + [Paragraph(esc(lbl), s['th']) for lbl in SKALA]
    rows = [header]
    for q in QUESTIONS:
        nr = q['nr']
        odp = answers.get(nr)
        col = (5 - odp) if odp in (1, 2, 3, 4, 5) else None  # 5->0 ... 1->4
        cells = [Paragraph(f"{nr}. {esc(q['pytanie'])}", s['td'])]
        for i in range(5):
            cells.append(Paragraph("<b>X</b>" if col == i else "", s['td_c']))
        rows.append(cells)

    col_w = [247] + [53, 53, 53, 53, 53]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 10))

    uwagi = (data.get('uwagi') or '').strip()
    uwagi_txt = f"<b>{esc(uwagi)}</b>" if uwagi else "…" * 90
    story.append(Paragraph(f"Dodatkowe uwagi dotyczące przebiegu praktyki zawodowej: {uwagi_txt}", s['body']))
    story.append(Spacer(1, 12))

    # Metryczka (bez danych osobowych - ankieta anonimowa)
    studia = (data.get('forma_studiow') or '').strip()
    studia_txt = studia if studia else "stacjonarne / niestacjonarne*"
    m = [
        [Paragraph("Rok akademicki", s['td']), Paragraph(f"<b>{esc(data.get('rok_akademicki', ''))}</b>", s['td'])],
        [Paragraph("Kierunek studiów", s['td']), Paragraph(f"<b>{esc(data.get('kierunek', 'informatyka'))}</b>", s['td'])],
        [Paragraph("Forma studiów", s['td']), Paragraph(f"<b>{esc(studia_txt)}</b>", s['td'])],
        [Paragraph("Semestr studiów", s['td']), Paragraph(f"<b>{esc(str(data.get('semestr', '')))}</b>", s['td'])],
        [Paragraph("Liczba godzin zrealizowanej praktyki zawodowej", s['td']),
         Paragraph(f"<b>{esc(str(data.get('godziny', '')))}</b>", s['td'])],
    ]
    mt = Table(m, colWidths=[300, 211])
    mt.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(mt)
    story.append(Spacer(1, 8))
    story.append(Paragraph("*niewłaściwe skreślić", s['foot']))
    story.append(Spacer(1, 10))
    from reportlab.lib.styles import ParagraphStyle
    podziekowanie = ParagraphStyle('Z5Thanks', parent=s['header'], alignment=2)  # pogrubione, do prawej
    story.append(Paragraph("Dziękujemy za udział w badaniu", podziekowanie))

    doc.build(story, canvasmaker=PageNumberCanvas)
