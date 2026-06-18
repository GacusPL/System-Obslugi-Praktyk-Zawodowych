from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from app.pdf.base import PageNumberCanvas
from app.pdf._common import esc, doc_styles, header_flowables


def generate_zal_nr4b(filepath, data):
    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=50, leftMargin=50,
                            topMargin=48, bottomMargin=54,
                            title="Załącznik nr 4b - Wniosek o zaliczenie praktyki na podstawie doświadczenia")
    s = doc_styles()
    story = header_flowables(s, "Załącznik nr 4b")
    story.append(Spacer(1, 6))
    story.append(Paragraph("WNIOSEK O ZALICZENIE PRAKTYKI<br/>NA PODSTAWIE DOŚWIADCZENIA ZAWODOWEGO", s['title']))

    # Metryczka
    story.append(Paragraph(f"Student / ka: <b>{esc(data.get('student_name', ''))}</b>", s['body']))
    story.append(Paragraph(f"Nr albumu: <b>{esc(data.get('nr_albumu', ''))}</b>", s['body']))
    story.append(Paragraph(f"Kierunek studiów: <b>{esc(data.get('kierunek', 'Informatyka'))}</b>", s['body']))
    story.append(Paragraph(f"Specjalność: <b>{esc(data.get('specjalnosc', '') or '—')}</b>", s['body']))
    story.append(Spacer(1, 10))

    typ_map = {
        'praca_zawodowa': 'Praca zawodowa (zatrudnienie)',
        'staz': 'Staż / praktyka zewnętrzna',
        'dzialalnosc_gospodarcza': 'Prowadzenie własnej działalności gospodarczej',
    }
    typ_text = typ_map.get(data.get('typ', ''), data.get('typ', '') or '—')
    story.append(Paragraph(f"Wnioskowana forma zaliczenia: <b>{esc(typ_text)}</b>", s['body']))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Uzasadnienie wniosku:", s['section']))
    uz = (data.get('uzasadnienie') or '').strip()
    story.append(Paragraph(f"<b>{esc(uz)}</b>" if uz else "…" * 90, s['body']))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Załączone dokumenty:", s['section']))
    zalaczniki = data.get('zalaczniki', [])
    if zalaczniki:
        for idx, z in enumerate(zalaczniki, start=1):
            story.append(Paragraph(f"{idx}. <b>{esc(z)}</b>", s['body']))
    else:
        story.append(Paragraph("Brak załączników.", s['body']))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Opinia Komisji Dydaktycznej:", s['section']))
    op = (data.get('opinia_komisji') or '').strip()
    story.append(Paragraph(f"<b>{esc(op)}</b>" if op else "…" * 90, s['body']))
    story.append(Spacer(1, 12))

    decision_map = {
        'zgoda_pelna': 'Zgoda pełna na zaliczenie praktyki',
        'zgoda_czesciowa': 'Zgoda częściowa (wymagane uzupełnienie brakujących efektów)',
        'odmowa': 'Odmowa zaliczenia praktyki',
    }
    dec = decision_map.get(data.get('decyzja', ''), '')
    dec_html = f"<b>{esc(dec)}</b>" if dec else ("…" * 40)
    story.append(Paragraph(f"Decyzja Dyrektora Instytutu: {dec_html}", s['body']))
    story.append(Spacer(1, 30))

    sig = Table([[Paragraph("……………………………………<br/>Podpis Dyrektora", s['cap']),
                  Paragraph("……………………………………<br/>Podpisy Członków Komisji", s['cap'])]],
                colWidths=[247, 248])
    sig.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                             ('TOPPADDING', (0, 0), (-1, -1), 10)]))
    story.append(sig)

    doc.build(story, canvasmaker=PageNumberCanvas)
