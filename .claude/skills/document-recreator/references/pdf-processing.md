# PDF Processing Reference

## Table of Contents
1. [Reading PDFs](#reading)
2. [Creating PDFs with ReportLab](#creating)
3. [Form Filling](#forms)
4. [Text and Table Extraction](#extraction)
5. [Command-Line Tools](#cli)

## Reading PDFs <a id="reading"></a>

### pypdf — Merge, split, metadata
```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader('input.pdf')
print(len(reader.pages))
page = reader.pages[0]
text = page.extract_text()
```

### pdfplumber — Text and table extraction with coordinates
```python
import pdfplumber

with pdfplumber.open('input.pdf') as pdf:
    page = pdf.pages[0]
    text = page.extract_text()
    tables = page.extract_tables()
    # Character-level data with positions
    chars = page.chars
```

## Creating PDFs with ReportLab <a id="creating"></a>

### Basic document
```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

doc = SimpleDocTemplate("output.pdf", pagesize=letter)
styles = getSampleStyleSheet()
elements = []

elements.append(Paragraph("Title", styles['Title']))
elements.append(Spacer(1, 12))
elements.append(Paragraph("Body text here.", styles['Normal']))

doc.build(elements)
```

### Tables with styling
```python
data = [
    ['Name', 'Score', 'Grade'],
    ['Alice', '95', 'A'],
    ['Bob', '87', 'B+'],
]

table = Table(data, colWidths=[2*inch, 1.5*inch, 1*inch])
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 14),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
]))
elements.append(table)
```

### Important: Avoid Unicode subscript/superscript characters in ReportLab
Use XML markup tags instead for proper rendering:
- Use `<sub>text</sub>` instead of Unicode subscripts
- Use `<super>text</super>` instead of Unicode superscripts

## Form Filling <a id="forms"></a>

### Fillable PDF forms
1. Check if fillable: `python3 scripts/pdf/check_fillable_fields.py input.pdf`
2. Extract fields: `python3 scripts/pdf/extract_form_field_info.py input.pdf fields.json`
3. Create field_values.json with values for each field_id
4. Fill: `python3 scripts/pdf/fill_fillable_fields.py input.pdf field_values.json output.pdf`

### Non-fillable forms (annotation method)
1. Extract structure: `python3 scripts/pdf/extract_form_structure.py input.pdf structure.json`
2. Convert to images: `python3 scripts/pdf/convert_pdf_to_images.py input.pdf images/`
3. Create fields.json with bounding boxes and text
4. Validate: `python3 scripts/pdf/check_bounding_boxes.py fields.json`
5. Fill: `python3 scripts/pdf/fill_pdf_form_with_annotations.py input.pdf fields.json output.pdf`

### fields.json format for non-fillable forms
```json
{
  "pages": [
    {"page_number": 1, "pdf_width": 612, "pdf_height": 792}
  ],
  "form_fields": [
    {
      "page_number": 1,
      "description": "Last name entry field",
      "field_label": "Last Name",
      "label_bounding_box": [43, 63, 87, 73],
      "entry_bounding_box": [92, 63, 260, 79],
      "entry_text": {"text": "Smith", "font_size": 10}
    }
  ]
}
```

## Text and Table Extraction <a id="extraction"></a>

### pdfplumber table extraction
```python
import pdfplumber

with pdfplumber.open('input.pdf') as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                print(row)
```

### pypdfium2 — Fast rendering
```python
import pypdfium2 as pdfium

pdf = pdfium.PdfDocument('input.pdf')
page = pdf[0]
bitmap = page.render(scale=2)
pil_image = bitmap.to_pil()
pil_image.save('page.png')
```

## Command-Line Tools <a id="cli"></a>

### pdftotext (poppler-utils)
```bash
pdftotext input.pdf output.txt        # Extract text
pdftotext -layout input.pdf output.txt # Preserve layout
```

### pdftoppm (poppler-utils)
```bash
pdftoppm -png -r 300 input.pdf output  # Convert to PNG at 300 DPI
```

### qpdf
```bash
qpdf input.pdf --pages . 1-5 -- output.pdf  # Extract pages
qpdf --merge a.pdf b.pdf -- merged.pdf       # Merge PDFs
```
