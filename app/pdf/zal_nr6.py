from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from app.pdf.base import PageNumberCanvas
from app.pdf._common import esc, doc_styles, header_flowables


def generate_zal_nr6(filepath, data):
    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=42, leftMargin=42,
                            topMargin=48, bottomMargin=54,
                            title="Załącznik nr 6 - Dziennik praktyki zawodowej")
    s = doc_styles()
    story = header_flowables(s, "Załącznik nr 6")
    story.append(Spacer(1, 6))
    story.append(Paragraph("DZIENNIK PRAKTYKI ZAWODOWEJ", s['title']))

    studia = (data.get('forma_studiow') or '').strip()
    studia_txt = f"inżynierskie, {studia}" if studia else "inżynierskie, stacjonarne"
    story.append(Paragraph(
        f"Student: <b>{esc(data.get('student_name', ''))}</b>"
        f"&nbsp;&nbsp;&nbsp;&nbsp;Nr albumu: <b>{esc(data.get('nr_albumu', ''))}</b>", s['body']))
    story.append(Paragraph(f"Kierunek: <b>{esc(data.get('kierunek', 'informatyka'))}</b>", s['body']))
    story.append(Paragraph(f"W zakresie: <b>{esc(data.get('specjalnosc', '') or '—')}</b>", s['body']))
    story.append(Paragraph(
        f"Studia: <b>{esc(studia_txt)}</b>&nbsp;&nbsp;&nbsp;&nbsp;Rok ak.: <b>{esc(data.get('rok_akademicki', ''))}</b>", s['body']))
    story.append(Paragraph(f"Miejsce odbywania praktyki: <b>{esc(data.get('zaklad_nazwa', ''))}</b>", s['body']))
    story.append(Paragraph("(nazwa instytucji – zakładu pracy)", s['cap_l']))
    story.append(Paragraph(
        f"Data rozpoczęcia praktyki: <b>{esc(data.get('termin_od', ''))}</b>"
        f"&nbsp;&nbsp;&nbsp;&nbsp;Data zakończenia praktyki: <b>{esc(data.get('termin_do', ''))}</b>", s['body']))
    story.append(Spacer(1, 12))

    # Miejsce na podpis studenta (po prawej, nad tabelą)
    student_sig = Table([[Paragraph("…" * 16, s['body'])],
                         [Paragraph("podpis studenta", s['cap'])]], colWidths=[220])
    student_sig.hAlign = 'RIGHT'
    student_sig.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                     ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    story.append(student_sig)
    story.append(Spacer(1, 10))

    # Tabela dziennika
    header = [
        Paragraph("Dzień", s['th']),
        Paragraph("Data", s['th']),
        Paragraph("Opis wykonanych prac", s['th']),
        Paragraph("Nr efektów uczenia się", s['th']),
        Paragraph("Podpis osoby nadzorującej", s['th']),
    ]
    rows = [header]
    for w in sorted(data.get('wpisy', []), key=lambda x: x.get('dzien_nr', 0)):
        efekty = ", ".join(str(n) for n in w.get('efekty', []))
        rows.append([
            Paragraph(f"<b>{w.get('dzien_nr', '')}</b>", s['td_c']),
            Paragraph(f"<b>{esc(w.get('data_wpisu', ''))}</b>", s['td_c']),
            Paragraph(f"<b>{esc(w.get('opis_prac', ''))}</b>", s['td']),
            Paragraph(f"<b>{esc(efekty)}</b>", s['td_c']),
            Paragraph("", s['td_c']),  # miejsce na ręczny podpis osoby nadzorującej
        ])
    if len(rows) == 1:
        rows.append([Paragraph("", s['td']), Paragraph("", s['td']),
                     Paragraph("Brak wpisów w dzienniku.", s['td']),
                     Paragraph("", s['td']), Paragraph("", s['td'])])

    tbl = Table(rows, colWidths=[34, 62, 279, 70, 66], repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4), ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(tbl)

    doc.build(story, canvasmaker=PageNumberCanvas)
