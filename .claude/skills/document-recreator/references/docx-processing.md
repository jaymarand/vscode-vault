# DOCX Processing Reference

## Table of Contents
1. [Creating documents](#creating)
2. [Reading existing documents](#reading)
3. [Tables](#tables)
4. [Styles and formatting](#styles)
5. [Headers, footers, and page setup](#page-setup)
6. [Images](#images)
7. [Lists](#lists)
8. [Advanced: XML editing workflow](#xml-editing)

## Creating documents <a id="creating"></a>

```python
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = Document()

# Headings
doc.add_heading('Document Title', level=0)
doc.add_heading('Section', level=1)
doc.add_heading('Subsection', level=2)

# Paragraphs
p = doc.add_paragraph('Normal text.')
p.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Bold/italic runs within a paragraph
p = doc.add_paragraph()
p.add_run('Bold text').bold = True
p.add_run(' and ')
p.add_run('italic text').italic = True

# Page break
doc.add_page_break()

doc.save('output.docx')
```

## Reading existing documents <a id="reading"></a>

```python
from docx import Document

doc = Document('existing.docx')

# Read all paragraphs
for para in doc.paragraphs:
    print(para.text)
    print(f"  Style: {para.style.name}")

# Read all tables
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            print(cell.text)

# Access sections (page setup)
for section in doc.sections:
    print(f"Page width: {section.page_width}")
    print(f"Page height: {section.page_height}")
```

## Tables <a id="tables"></a>

```python
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

# Basic table
table = doc.add_table(rows=3, cols=4)
table.style = 'Table Grid'

# Set header row
header = table.rows[0].cells
header[0].text = 'Name'
header[1].text = 'Department'
header[2].text = 'Score'
header[3].text = 'Grade'

# Add data
row = table.rows[1].cells
row[0].text = 'Alice'
row[1].text = 'Engineering'
row[2].text = '95'
row[3].text = 'A'

# Set column widths
for row in table.rows:
    row.cells[0].width = Inches(2)
    row.cells[1].width = Inches(2)
    row.cells[2].width = Inches(1)
    row.cells[3].width = Inches(1)

# Cell shading
def set_cell_shading(cell, color):
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color)
    shading.set(qn('w:val'), 'clear')
    cell._tc.get_or_add_tcPr().append(shading)

# Shade header row
for cell in table.rows[0].cells:
    set_cell_shading(cell, '4472C4')
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.bold = True

# Merge cells
table.cell(0, 0).merge(table.cell(0, 1))

doc.save('output.docx')
```

## Styles and formatting <a id="styles"></a>

```python
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Font formatting
p = doc.add_paragraph()
run = p.add_run('Formatted text')
run.font.name = 'Arial'
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0, 0, 255)
run.font.bold = True
run.font.italic = True
run.font.underline = True

# Paragraph formatting
p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
p.paragraph_format.space_before = Pt(6)
p.paragraph_format.space_after = Pt(6)
p.paragraph_format.line_spacing = Pt(18)
p.paragraph_format.left_indent = Inches(0.5)
p.paragraph_format.first_line_indent = Inches(0.25)

# Apply built-in styles
doc.add_paragraph('Quote text', style='Quote')
doc.add_paragraph('Intense Quote', style='Intense Quote')

doc.save('output.docx')
```

## Headers, footers, and page setup <a id="page-setup"></a>

```python
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.section import WD_ORIENT

doc = Document()
section = doc.sections[0]

# US Letter size (default is A4)
section.page_width = Inches(8.5)
section.page_height = Inches(11)

# Margins
section.top_margin = Inches(1)
section.bottom_margin = Inches(1)
section.left_margin = Inches(1)
section.right_margin = Inches(1)

# Landscape orientation
section.orientation = WD_ORIENT.LANDSCAPE
# Swap width/height for landscape
section.page_width, section.page_height = section.page_height, section.page_width

# Header
header = section.header
header.is_linked_to_previous = False
p = header.paragraphs[0]
p.text = 'Document Header'

# Footer
footer = section.footer
footer.is_linked_to_previous = False
p = footer.paragraphs[0]
p.text = 'Page Footer'

doc.save('output.docx')
```

## Images <a id="images"></a>

```python
from docx import Document
from docx.shared import Inches

doc = Document()
doc.add_picture('image.png', width=Inches(4))

# Image in a table cell
table = doc.add_table(rows=1, cols=2)
cell = table.cell(0, 0)
p = cell.paragraphs[0]
run = p.add_run()
run.add_picture('logo.png', width=Inches(1.5))

doc.save('output.docx')
```

## Lists <a id="lists"></a>

```python
from docx import Document

doc = Document()

# Bullet list
doc.add_paragraph('Item 1', style='List Bullet')
doc.add_paragraph('Item 2', style='List Bullet')
doc.add_paragraph('Sub-item', style='List Bullet 2')

# Numbered list
doc.add_paragraph('Step 1', style='List Number')
doc.add_paragraph('Step 2', style='List Number')
doc.add_paragraph('Sub-step', style='List Number 2')

doc.save('output.docx')
```

Never insert unicode bullet characters manually. Always use the built-in list styles.

## Advanced: XML editing workflow <a id="xml-editing"></a>

For complex edits that python-docx can't handle (tracked changes, comments, precise formatting):

### Unpack
```bash
python scripts/docx/unpack.py document.docx unpacked/
```
This extracts the DOCX (which is a ZIP), pretty-prints XML, and merges adjacent runs.

### Edit XML
Edit files in `unpacked/word/`:
- `document.xml` — main document content
- `styles.xml` — style definitions
- `header1.xml`, `footer1.xml` — headers/footers
- `numbering.xml` — list definitions

### Pack
```bash
python scripts/docx/pack.py unpacked/ output.docx --original document.docx
```
Validates, condenses XML, and creates the DOCX file.

### Dependencies for XML workflow
```bash
pip3 install defusedxml
```

### Tracked changes
- Insertions: `<w:ins w:author="Author" w:date="2024-01-01T00:00:00Z">...</w:ins>`
- Deletions: `<w:del>...<w:delText>deleted text</w:delText>...</w:del>`

### Comments
Use the comment.py script:
```bash
python scripts/docx/comment.py unpacked/ 0 "Comment text"
python scripts/docx/comment.py unpacked/ 1 "Reply text" --parent 0
```

### Smart quotes
Use XML entities in XML files:
- `&#x201C;` and `&#x201D;` for double quotes
- `&#x2018;` and `&#x2019;` for single quotes/apostrophes
