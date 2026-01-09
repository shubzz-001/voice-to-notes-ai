from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import textwrap

def export_pdf(text: str, output_path: str):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    y = height - 40
    for line in textwrap.wrap(text, 90):
        c.drawString(40, y, line)
        y -= 14
        if y < 40:
            c.showPage()
            y = height - 40

    c.save()
