from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas
import textwrap


def export_pdf(text: str, output_path: str):
    """
    Export text to a well-formatted PDF with proper styling
    """
    try:
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Container for the 'Flowable' objects
        story = []

        # Define styles
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#1f77b4',
            spaceAfter=30,
            alignment=TA_CENTER
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor='#2c3e50',
            spaceAfter=12,
            spaceBefore=12
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )

        # Split text into sections
        lines = text.split('\n')

        for line in lines:
            line = line.strip()

            if not line:
                story.append(Spacer(1, 0.2 * inch))
                continue

            # Detect headings (lines ending with :)
            if line.endswith(':') and len(line) < 100:
                story.append(Paragraph(line, heading_style))
            # Detect titles (all caps or very short lines)
            elif line.isupper() and len(line) < 50:
                story.append(Paragraph(line, title_style))
            # Regular paragraph
            else:
                # Escape special characters for ReportLab
                line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(line, body_style))

        # Build PDF
        doc.build(story)

    except Exception as e:
        # Fallback to simple text wrapping if advanced PDF fails
        print(f"Advanced PDF generation failed: {e}. Using simple method.")
        export_pdf_simple(text, output_path)


def export_pdf_simple(text: str, output_path: str):
    """
    Simple fallback PDF export using basic canvas
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "Lecture Notes")

    # Content
    c.setFont("Helvetica", 10)
    y = height - 120

    for line in textwrap.wrap(text, width=90):
        if y < 72:  # Bottom margin
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 72

        c.drawString(72, y, line)
        y -= 14

    c.save()