from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os

class NumberedCanvas(canvas.Canvas):
    """
    Canvas to handle two-pass rendering for page numbers (Strona X z Y)
    and drawing common headers/footers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Arial", 8)
        self.setFillColor(colors.HexColor("#64748b")) # slate text
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 785, "SOPZ - System Obsługi Praktyk Zawodowych")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(54, 777, 541, 777)
            
        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(54, 55, 541, 55)
        
        page_text = f"Strona {self._pageNumber} z {page_count}"
        self.drawRightString(541, 40, page_text)
        self.drawString(54, 40, "Akademia Nauk Stosowanych w Elblągu")
        self.restoreState()


class PageNumberCanvas(canvas.Canvas):
    """Stopka jako sam numer strony w formacie X/Y (bez tekstu instytucji)."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.saveState()
            self.setFont("Arial", 9)
            self.setFillColor(colors.black)
            self.drawCentredString(A4[0] / 2.0, 32, f"{self._pageNumber}/{num_pages}")
            self.restoreState()
            super().showPage()
        super().save()


def get_premium_styles():
    styles = getSampleStyleSheet()
    
    # Custom styles supporting Polish characters with registered Arial font
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Arial-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1e293b"),
        alignment=1, # Center
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        alignment=1, # Center
        spaceAfter=25
    )
    
    h1_style = ParagraphStyle(
        'DocH1',
        parent=styles['Normal'],
        fontName='Arial-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=15,
        spaceAfter=10
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Normal'],
        fontName='Arial-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155")
    )
    
    label_style = ParagraphStyle(
        'DocLabel',
        parent=styles['Normal'],
        fontName='Arial-Bold',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#0f172a")
    )

    table_header_style = ParagraphStyle(
        'DocTableHeader',
        parent=styles['Normal'],
        fontName='Arial-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )

    table_body_style = ParagraphStyle(
        'DocTableBody',
        parent=styles['Normal'],
        fontName='Arial',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#334155")
    )

    return {
        'Title': title_style,
        'Subtitle': subtitle_style,
        'H1': h1_style,
        'H2': h2_style,
        'Body': body_style,
        'Label': label_style,
        'TableHeader': table_header_style,
        'TableBody': table_body_style
    }
