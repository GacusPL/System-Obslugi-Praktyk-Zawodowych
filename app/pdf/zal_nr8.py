from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from app.pdf.base import PageNumberCanvas
from app.pdf._common import esc, doc_styles, header_flowables


def _score(v):
    if v is None:
        return ''
    return f"{v:.1f}" if isinstance(v, float) else str(v)


def generate_zal_nr8(filepath, data):
    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=50, leftMargin=50,
                            topMargin=48, bottomMargin=54,
                            title="Załącznik nr 8 - Protokół egzaminu praktyki zawodowej")
    s = doc_styles()
    story = header_flowables(s, "Załącznik nr 8")
    story.append(Spacer(1, 6))
    story.append(Paragraph("PROTOKÓŁ EGZAMINU PRAKTYKI ZAWODOWEJ", s['title']))

    # Metryczka
    story.append(Paragraph(
        f"Student / ka: <b>{esc(data.get('student_name', ''))}</b>"
        f"&nbsp;&nbsp;&nbsp;&nbsp;Nr albumu: <b>{esc(data.get('nr_albumu', ''))}</b>", s['body']))
    story.append(Paragraph(f"Kierunek studiów: <b>{esc(data.get('kierunek', 'Informatyka'))}</b>", s['body']))
    story.append(Paragraph(f"Data egzaminu: <b>{esc(data.get('data_egzaminu', '') or '—')}</b>", s['body']))
    story.append(Spacer(1, 12))

    # Komisja egzaminacyjna
    story.append(Paragraph("Komisja egzaminacyjna", s['section']))
    komisja = data.get('komisja', [])
    if komisja:
        krows = [[Paragraph("Lp.", s['th']), Paragraph("Imię i nazwisko", s['th']), Paragraph("Funkcja w komisji", s['th'])]]
        for idx, k in enumerate(komisja, start=1):
            krows.append([
                Paragraph(str(idx), s['td_c']),
                Paragraph(f"<b>{esc(k.get('imie', ''))} {esc(k.get('nazwisko', ''))}</b>", s['td']),
                Paragraph(f"<b>{esc(k.get('rola_w_komisji', ''))}</b>", s['td']),
            ])
        kt = Table(krows, colWidths=[34, 270, 191], repeatRows=1)
        kt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(kt)
    else:
        story.append(Paragraph("Brak wyznaczonej komisji.", s['body']))
    story.append(Spacer(1, 14))

    # Zestawienie ocen
    story.append(Paragraph("Zestawienie ocen i ocena końcowa", s['section']))

    def cell(v):
        sc = _score(v)
        return Paragraph(f"<b>{esc(sc)}</b>" if sc else "…………", s['td_c'])

    gr = [
        [Paragraph("Część składowa", s['th']), Paragraph("Ocena (2–5)", s['th'])],
        [Paragraph("Ocena z egzaminu ustnego", s['td']), cell(data.get('ocena_ustna'))],
        [Paragraph("Ocena końcowa z praktyki", s['td']), cell(data.get('ocena_koncowa'))],
    ]
    gt = Table(gr, colWidths=[395, 100])
    gt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(gt)
    story.append(Spacer(1, 30))

    # Podpisy
    sig = Table([[Paragraph("……………………………………<br/>Podpis Przewodniczącego Komisji", s['cap']),
                  Paragraph("……………………………………<br/>Podpisy Członków Komisji", s['cap'])]],
                colWidths=[247, 248])
    sig.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                             ('TOPPADDING', (0, 0), (-1, -1), 10)]))
    story.append(sig)

    doc.build(story, canvasmaker=PageNumberCanvas)
