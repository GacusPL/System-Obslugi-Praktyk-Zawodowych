from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from app.pdf.base import get_premium_styles, PageNumberCanvas

DOTS = "…" * 30


def _esc(text):
    text = (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return text.replace('\n', '<br/>')


def _fld(value, dots=30):
    """Zwraca wartość pogrubioną albo kropkowaną linię do wypełnienia."""
    value = '' if value is None else str(value).strip()
    return f"<b>{_esc(value)}</b>" if value else ("…" * dots)


def generate_zal_nr3(filepath, data):
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=54,
        leftMargin=54,
        topMargin=48,
        bottomMargin=54,
        title="Załącznik nr 3 - Karta praktyki zawodowej"
    )

    styles = get_premium_styles()
    italic_font = 'Arial-Italic' if 'Arial-Italic' in pdfmetrics.getRegisteredFontNames() else 'Arial'

    zal_no = ParagraphStyle('Z3No', parent=styles['Body'], fontSize=10, leading=13, alignment=2, textColor=colors.black)
    header_inst = ParagraphStyle('Z3Head', parent=styles['Body'], fontName='Arial-Bold', fontSize=11,
                                 leading=15, alignment=0, textColor=colors.black)
    doc_title = ParagraphStyle('Z3Title', parent=styles['Title'], fontSize=14, leading=18, alignment=1,
                               spaceBefore=6, spaceAfter=10, textColor=colors.black)
    section = ParagraphStyle('Z3Section', parent=styles['Body'], fontName='Arial-Bold', fontSize=12,
                             leading=16, alignment=1, spaceBefore=14, spaceAfter=8, textColor=colors.black)
    body = ParagraphStyle('Z3Body', parent=styles['Body'], fontSize=10.5, leading=18, textColor=colors.black)
    cap = ParagraphStyle('Z3Cap', parent=styles['Body'], fontName=italic_font, fontSize=8.5, leading=11,
                         alignment=1, textColor=colors.HexColor("#555555"))
    cap_l = ParagraphStyle('Z3CapL', parent=cap, alignment=0)
    foot = ParagraphStyle('Z3Foot', parent=styles['Body'], fontName=italic_font, fontSize=9, leading=12,
                          textColor=colors.black)

    studia = (data.get('forma_studiow') or '').strip()
    studia_txt = f"inżynierskie {studia}" if studia else "inżynierskie stacjonarne / niestacjonarne*"

    story = []

    # Numer + nagłówek
    story.append(Paragraph("Załącznik nr 3", zal_no))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Akademia Nauk Stosowanych w Elblągu", header_inst))
    story.append(Paragraph("Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego", header_inst))
    story.append(Spacer(1, 6))
    story.append(Paragraph("KARTA PRAKTYKI ZAWODOWEJ", doc_title))

    # ---- SKIEROWANIE NA PRAKTYKĘ ----
    story.append(Paragraph("SKIEROWANIE NA PRAKTYKĘ", section))
    story.append(Paragraph(
        f"Na podstawie porozumienia nr {_fld(data.get('porozumienie_nr'), 8)}, z dnia "
        f"{'…' * 14} r., kieruję niżej wymienionego studenta na praktykę zawodową do zakładu pracy:", body))
    story.append(Paragraph(_fld(data.get('zaklad_nazwa'), 60), body))
    story.append(Paragraph("(nazwa instytucji (zakładu pracy))", cap_l))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"Imię i nazwisko: {_fld(data.get('student_name'), 50)}", body))
    story.append(Paragraph(f"Numer albumu: {_fld(data.get('nr_albumu'), 40)}", body))
    story.append(Paragraph(f"Studia: {_esc(studia_txt)}", body))
    story.append(Paragraph(f"Kierunek: <b>{_esc(data.get('kierunek', 'informatyka'))}</b>", body))
    story.append(Paragraph(f"specjalność: {_fld(data.get('specjalnosc'), 45)}", body))
    story.append(Paragraph("Czas trwania praktyki: <b>6 miesięcy</b> (120 dni roboczych)", body))
    story.append(Paragraph(f"Uczelniany opiekun praktyki zawodowej: {_fld(data.get('uopz_name'), 35)}", body))
    story.append(Paragraph(
        f"Termin praktyki: od {_fld(data.get('termin_od'), 16)} do {_fld(data.get('termin_do'), 16)} r.", body))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Dyrektor Instytutu lub osoba upoważniona", body))
    story.append(Spacer(1, 16))
    story.append(Paragraph("…" * 40, body))
    story.append(Paragraph("(podpis)", cap_l))
    story.append(Spacer(1, 8))

    story.append(Paragraph(f"Zakładowy opiekun praktyki zawodowej: {'…' * 30}", body))
    story.append(Paragraph("(imię i nazwisko, funkcja, zajmowane stanowisko)", cap_l))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Potwierdzam zgłoszenie się studenta na praktykę:", body))
    story.append(Paragraph("…" * 40, body))
    story.append(Paragraph("(data, pieczęć i podpis zakładowego opiekuna praktyki)", cap_l))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Potwierdzam odbycie szkolenia BHP:", body))
    story.append(Paragraph("…" * 40, body))
    story.append(Paragraph("(data, pieczęć i podpis upoważnionego pracownika zakładu)", cap_l))

    # ---- ZAŚWIADCZENIE (trzymane razem, by nie dzielić sekcji między strony) ----
    cd_table = Table([[Paragraph("…" * 22, body), Paragraph("…" * 22, body)],
                      [Paragraph("(miejscowość i data)", cap), Paragraph("(pieczęć i podpis kierownika zakładu)", cap)]],
                     colWidths=[243, 244])
    cd_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                  ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    story.append(KeepTogether([
        Paragraph("Zaświadczenie odbycia praktyki zawodowej", section),
        Paragraph(
            f"Zaświadczam, że student {_fld(data.get('student_name'), 40)} odbył praktykę zawodową w "
            f"{_fld(data.get('zaklad_nazwa'), 40)} w okresie (okresach) od {_fld(data.get('termin_od'), 14)} do "
            f"{_fld(data.get('termin_do'), 14)} zgodnie z przyjętym programem.", body),
        Paragraph(f"Uwagi: {'…' * 55}", body),
        Paragraph("…" * 70, body),
        Spacer(1, 22),
        cd_table,
    ]))

    # ---- OCENA PRZEBIEGU (każdy blok trzymany razem) ----
    story.append(KeepTogether([
        Paragraph("Ocena przebiegu praktyki zawodowej", section),
        Paragraph(f"Ocena parametryczna (w skali 2 do 5): {_fld(_score(data.get('ocena_param_zopz')), 18)}", body),
        Paragraph("Ocena opisowa:", body),
        _opis(data.get('ocena_opisowa_zopz'), body),
        Spacer(1, 6),
        _right_caption("Zakładowy opiekun praktyki zawodowej:", "(data, pieczęć i podpis)", body, cap),
    ]))
    story.append(Spacer(1, 14))

    story.append(KeepTogether([
        Paragraph(f"Ocena parametryczna (w skali 2 do 5): {_fld(_score(data.get('ocena_param_uopz')), 18)}", body),
        Paragraph("Ocena opisowa:", body),
        _opis(data.get('ocena_opisowa_uopz'), body),
        Spacer(1, 6),
        _right_caption("Uczelniany opiekun praktyki zawodowej:", "(data, pieczęć i podpis)", body, cap),
    ]))
    story.append(Spacer(1, 14))

    story.append(KeepTogether([
        Paragraph(
            f"Ocena sprawozdania z praktyki (w skali 2 do 5): {_fld(_score(data.get('ocena_sprawozdania')), 18)}", body),
        Spacer(1, 14),
        Paragraph("…" * 35, body),
        Paragraph("(data i podpis uczelnianego opiekuna praktyki)", cap_l),
    ]))

    story.append(Spacer(1, 12))
    story.append(Paragraph("*) niewłaściwe skreślić", foot))

    doc.build(story, canvasmaker=PageNumberCanvas)


def _score(v):
    if v is None:
        return ''
    return f"{v:.1f}" if isinstance(v, float) else str(v)


def _opis(text, body):
    text = (text or '').strip()
    if text:
        # Tekst z systemu - pogrubiony dla odróżnienia od szablonu
        return Paragraph(f"<b>{_esc(text)}</b>", body)
    return Paragraph("<br/>".join(["…" * 70] * 4), body)


def _right_caption(label, caption, body, cap):
    t = Table([[Paragraph(label, body), Paragraph("…" * 16, body)],
               ["", Paragraph(caption, cap)]], colWidths=[280, 207])
    t.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                           ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                           ('LEFTPADDING', (0, 0), (-1, -1), 0), ('RIGHTPADDING', (0, 0), (-1, -1), 0)]))
    return t
