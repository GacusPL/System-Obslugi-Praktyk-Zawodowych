import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 1. Register fonts supporting Polish characters
try:
    windir = os.environ.get('WINDIR', 'C:\\Windows')
    
    font_paths = [
        os.path.join(windir, 'Fonts', 'arial.ttf'),
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/msttcorefonts/arial.ttf',
    ]
    
    font_bold_paths = [
        os.path.join(windir, 'Fonts', 'arialbd.ttf'),
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/msttcorefonts/arialbd.ttf',
    ]

    font_italic_paths = [
        os.path.join(windir, 'Fonts', 'ariali.ttf'),
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf',
        '/usr/share/fonts/truetype/msttcorefonts/ariali.ttf',
    ]

    registered = False
    for path in font_paths:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont('Arial', path))
            registered = True
            break
            
    registered_bold = False
    for path in font_bold_paths:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont('Arial-Bold', path))
            registered_bold = True
            break

    for path in font_italic_paths:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont('Arial-Italic', path))
            break

    # Zarejestruj rodzinę czcionek, aby znaczniki <b>/<i> w Paragraph
    # mapowały się na Arial-Bold / Arial-Italic (inaczej <b> nie pogrubia).
    if registered:
        registered_names = pdfmetrics.getRegisteredFontNames()
        bold_name = 'Arial-Bold' if 'Arial-Bold' in registered_names else 'Arial'
        italic_name = 'Arial-Italic' if 'Arial-Italic' in registered_names else 'Arial'
        pdfmetrics.registerFontFamily(
            'Arial', normal='Arial', bold=bold_name,
            italic=italic_name, boldItalic=bold_name
        )

    # Fallback to Helvetica if no suitable font is found
    if not registered:
        # reportlab default
        pass
except Exception as e:
    print(f"Error registering fonts: {e}")

# 2. Main PDF generation routing
def generate_pdf(typ, data):
    """
    Generate PDF document based on typ and data.
    typ: 'zal_nr2a', 'zal_nr3', 'zal_nr4', 'zal_nr4b', 'zal_nr5', 'zal_nr6', 'zal_nr7', 'zal_nr8'
    data: dict containing necessary fields for rendering
    returns: absolute path to generated PDF file
    """
    # Create target directory
    praktyka_id = data.get('praktyka_id', 'temp')
    # Save folder in app/storage/generated/<praktyka_id>/ (outside static for safety)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_dir = os.path.join(base_dir, 'storage', 'generated', str(praktyka_id))
    os.makedirs(target_dir, exist_ok=True)
    
    filepath = os.path.join(target_dir, f"{typ}.pdf")
    
    # Route to sub-generators
    if typ == 'zal_nr2a':
        from app.pdf.zal_nr2a import generate_zal_nr2a
        generate_zal_nr2a(filepath, data)
    elif typ == 'zal_nr3':
        from app.pdf.zal_nr3 import generate_zal_nr3
        generate_zal_nr3(filepath, data)
    elif typ == 'zal_nr4':
        from app.pdf.zal_nr4 import generate_zal_nr4
        generate_zal_nr4(filepath, data)
    elif typ == 'zal_nr4b':
        from app.pdf.zal_nr4b import generate_zal_nr4b
        generate_zal_nr4b(filepath, data)
    elif typ == 'zal_nr5':
        from app.pdf.zal_nr5 import generate_zal_nr5
        generate_zal_nr5(filepath, data)
    elif typ == 'zal_nr6':
        from app.pdf.zal_nr6 import generate_zal_nr6
        generate_zal_nr6(filepath, data)
    elif typ == 'zal_nr7':
        from app.pdf.zal_nr7 import generate_zal_nr7
        generate_zal_nr7(filepath, data)
    elif typ == 'zal_nr8':
        from app.pdf.zal_nr8 import generate_zal_nr8
        generate_zal_nr8(filepath, data)
    else:
        raise ValueError(f"Unknown PDF document type: {typ}")
        
    return filepath
