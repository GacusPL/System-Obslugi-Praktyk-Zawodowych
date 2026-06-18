from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from app.pdf.base import PageNumberCanvas
from app.pdf._common import esc, doc_styles, header_flowables


def generate_zal_nr4(filepath, data):
    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=50, leftMargin=50,
                            topMargin=48, bottomMargin=54,
                            title="Załącznik nr 4 - Potwierdzenie efektów uczenia się")
    s = doc_styles()
    story = header_flowables(s, "Załącznik nr 4")
    story.append(Spacer(1, 6))
    story.append(Paragraph("POTWIERDZENIE UZYSKANIA EFEKTÓW UCZENIA SIĘ<br/>W RAMACH PRAKTYKI ZAWODOWEJ", s['title']))

    # Metryczka
    story.append(Paragraph(f"Student / ka: <b>{esc(data.get('student_name', ''))}</b>", s['body']))
    story.append(Paragraph(f"Nr albumu: <b>{esc(data.get('nr_albumu', ''))}</b>", s['body']))
    story.append(Paragraph(f"Kierunek studiów: <b>{esc(data.get('kierunek', 'Informatyka'))}</b>", s['body']))
    story.append(Paragraph(f"Specjalność: <b>{esc(data.get('specjalnosc', '') or '—')}</b>", s['body']))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"W ramach praktyki zawodowej zrealizowanej w wymiarze <b>{esc(str(data.get('godziny_zrealizowane', '')))}</b> "
        f"godzin uzyskał/a / nie uzyskał/a* zakładane dla praktyki zawodowej efekty uczenia się:", s['body']))
    story.append(Spacer(1, 8))

    # Tabela efektów
    rows = [[Paragraph("Efekty uczenia się", s['th']), "", Paragraph("Potwierdzenie uzyskania efektów", s['th'])]]
    for e in data.get('efekty', []):
        if e.get('uzyskano'):
            potw = "<b>uzyskał/a</b><br/><strike>nie uzyskał/a</strike>"
        else:
            potw = "<strike>uzyskał/a</strike><br/><b>nie uzyskał/a</b>"
        rows.append([
            Paragraph(f"{int(e.get('nr', 0)):02d}", s['td_c']),
            Paragraph(esc(e.get('opis', '')), s['td']),
            Paragraph(potw, s['td_c'])
        ])
    tbl = Table(rows, colWidths=[28, 357, 110], repeatRows=1)
    tbl.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 16))

    # Potwierdzenie ZOPZ - miejsce na podpis po prawej stronie
    zopz_sig = Table([[Paragraph("…" * 18, s['body'])],
                      [Paragraph("Data, podpis i pieczęć zakładu pracy", s['cap'])]], colWidths=[250])
    zopz_sig.hAlign = 'RIGHT'
    zopz_sig.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                  ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    story.append(KeepTogether([
        Paragraph("Potwierdzenie bezpośredniego opiekuna zakładowego:", s['body']),
        Spacer(1, 18),
        zopz_sig,
    ]))
    story.append(Spacer(1, 14))

    # Opinia UOPZ
    opinia = (data.get('opinia_uopz') or '').strip()
    opinia_flow = Paragraph(f"<b>{esc(opinia)}</b>", s['body']) if opinia else Paragraph("<br/>".join(["…" * 80] * 3), s['body'])
    uopz_sig = Table([[Paragraph("…" * 18, s['body'])],
                      [Paragraph("Data, podpis opiekuna uczelnianego", s['cap'])]], colWidths=[250])
    uopz_sig.hAlign = 'RIGHT'
    uopz_sig.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                  ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    story.append(KeepTogether([
        Paragraph("Opinia opiekuna uczelnianego", s['section']),
        opinia_flow,
        Spacer(1, 18),
        uopz_sig,
    ]))

    story.append(Spacer(1, 10))
    story.append(Paragraph("*niewłaściwe skreślić", s['foot']))

    doc.build(story, canvasmaker=PageNumberCanvas)
