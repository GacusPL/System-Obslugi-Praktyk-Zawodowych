"""Wspólne elementy wiernego odwzorowania formularzy (Załączniki)."""
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from app.pdf.base import get_premium_styles


def esc(text):
    text = (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return text.replace('\n', '<br/>')


def italic_font():
    return 'Arial-Italic' if 'Arial-Italic' in pdfmetrics.getRegisteredFontNames() else 'Arial'


def doc_styles():
    """Style wspólne dla formularzy załączników."""
    base = get_premium_styles()
    it = italic_font()
    s = {
        'zal_no': ParagraphStyle('ZNo', parent=base['Body'], fontSize=10, leading=13, alignment=2, textColor=colors.black),
        'header': ParagraphStyle('ZHead', parent=base['Body'], fontName='Arial-Bold', fontSize=11, leading=15, alignment=0, textColor=colors.black),
        'title': ParagraphStyle('ZTitle', parent=base['Title'], fontSize=13.5, leading=18, alignment=1, spaceBefore=6, spaceAfter=10, textColor=colors.black),
        'section': ParagraphStyle('ZSection', parent=base['Body'], fontName='Arial-Bold', fontSize=12, leading=16, alignment=1, spaceBefore=14, spaceAfter=8, textColor=colors.black),
        'body': ParagraphStyle('ZBody', parent=base['Body'], fontSize=10.5, leading=17, textColor=colors.black),
        'th': ParagraphStyle('ZTH', parent=base['Body'], fontName='Arial-Bold', fontSize=9.5, leading=12, alignment=1, textColor=colors.black),
        'td': ParagraphStyle('ZTD', parent=base['Body'], fontSize=9, leading=12, textColor=colors.black),
        'td_c': ParagraphStyle('ZTDc', parent=base['Body'], fontSize=9, leading=12, alignment=1, textColor=colors.black),
        'cap': ParagraphStyle('ZCap', parent=base['Body'], fontName=it, fontSize=8.5, leading=11, alignment=1, textColor=colors.HexColor("#555555")),
        'cap_l': ParagraphStyle('ZCapL', parent=base['Body'], fontName=it, fontSize=8.5, leading=11, alignment=0, textColor=colors.HexColor("#555555")),
        'foot': ParagraphStyle('ZFoot', parent=base['Body'], fontName=it, fontSize=9, leading=12, textColor=colors.black),
    }
    return s


def header_flowables(s, zal_label):
    """Numer załącznika (prawy górny róg) + pogrubiony nagłówek instytutu (do lewej)."""
    return [
        Paragraph(zal_label, s['zal_no']),
        Spacer(1, 4),
        Paragraph("Akademia Nauk Stosowanych w Elblągu", s['header']),
        Paragraph("Instytut Informatyki Stosowanej im. Krzysztofa Brzeskiego", s['header']),
    ]
