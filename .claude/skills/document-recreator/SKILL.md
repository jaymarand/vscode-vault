---
name: document-recreator
description: "Recreate any document the user provides — reports, reviews, forms, spreadsheets, Word docs — using new data. Use this skill when the user says 'recreate this document,' 'fill out this form,' 'generate this report with new data,' 'make a new version of this,' 'use this template,' 'fill this in,' or provides a PDF/XLSX/DOCX/CSV template alongside data. Also triggers when the user mentions store reviews, weekly business reports, performance reviews, memos, letters, or any recurring document that needs to be regenerated with fresh data."
---

# Document Recreator

Recreate any document from a template using new data. Spawns a Sonnet subagent for cost-efficient processing while maintaining quality.

## When This Skill Activates

- User provides a document (PDF, XLSX, DOCX, CSV) and says "recreate this with new data"
- User provides a template and separate data source
- User asks to fill out a form, generate a report, or produce a review
- Recurring Goodwill documents: store reviews, weekly business reports, performance reviews

## Workflow

### Step 1: Analyze the Template

Read the provided document to understand its structure:

**For PDFs:**
1. Read the PDF using the Read tool to understand the layout
2. Check if it has fillable form fields:
   ```bash
   python3 scripts/pdf/check_fillable_fields.py <template.pdf>
   ```
3. If fillable, extract field info:
   ```bash
   python3 scripts/pdf/extract_form_field_info.py <template.pdf> field_info.json
   ```
4. If not fillable, extract form structure:
   ```bash
   python3 scripts/pdf/extract_form_structure.py <template.pdf> form_structure.json
   ```
5. Convert to images for visual analysis:
   ```bash
   python3 scripts/pdf/convert_pdf_to_images.py <template.pdf> template_images/
   ```

**For DOCX (Word documents):**
1. Read the document using python-docx to understand structure
2. Map out sections: headings, paragraphs, tables, headers/footers, images
3. Note styles, fonts, spacing, numbering, and any tracked changes
4. For editing existing DOCX files, use the unpack/edit/pack workflow (see references)

**For XLSX/CSV:**
1. Read with pandas or openpyxl to understand structure
2. Identify which cells are labels vs data entry points
3. Note any formulas, formatting, or conditional logic

**For any format:**
- Identify all fields/cells that need data
- Map the template structure: headers, sections, data entry points
- Note formatting rules, fonts, colors, column widths

### Step 2: Map Data to Template

Once you understand the template, map the user's data to template fields:

1. Present the user with a field mapping: "I found these fields in the template: [list]. Here's how I'll map your data."
2. Ask for confirmation or corrections before proceeding
3. Flag any fields where the data is missing or ambiguous

### Step 3: Spawn Sonnet Subagent to Generate

Use the Agent tool with `model: "sonnet"` to do the actual document generation. This keeps costs low for what is largely mechanical work.

The subagent prompt should include:
- The template structure (from Step 1)
- The mapped data (from Step 2)
- The output format and file path
- Instructions for the specific document type (see below)

```
Agent({
  description: "Recreate document with new data",
  model: "sonnet",
  prompt: "<include template structure, data mapping, and format-specific instructions>"
})
```

### Step 4: Verify Output

After the subagent completes:
- Read the output file to verify correctness
- For PDFs: convert to images and visually inspect
- For XLSX: check formulas recalculated correctly
- Present the output to the user for review

## Format-Specific Instructions

### PDF Output

**Fillable PDFs:**
1. Create `field_values.json` mapping field IDs to data values
2. Fill using: `python3 scripts/pdf/fill_fillable_fields.py <input.pdf> field_values.json <output.pdf>`

**Non-fillable PDFs (annotation method):**
1. Create `fields.json` with bounding box coordinates and text values
2. Validate: `python3 scripts/pdf/check_bounding_boxes.py fields.json`
3. Fill: `python3 scripts/pdf/fill_pdf_form_with_annotations.py <input.pdf> fields.json <output.pdf>`
4. Verify: `python3 scripts/pdf/convert_pdf_to_images.py <output.pdf> verify_images/`

**Creating new PDFs from scratch:**
Use reportlab for professional document creation:
```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
```

Read `references/pdf-processing.md` for detailed reportlab, pypdf, and pdfplumber usage.

### XLSX Output

1. Use openpyxl for files needing formulas and formatting
2. Use pandas for data-heavy files without complex formatting
3. Use Excel formulas, not hardcoded Python calculations — the spreadsheet should stay dynamic
4. After creating/editing, recalculate formulas:
   ```bash
   python3 scripts/xlsx/recalc.py <output.xlsx>
   ```
5. Check the JSON output for errors and fix any found

**Formatting standards:**
- Professional font (Arial or Times New Roman) unless template uses something else
- Match the template's formatting exactly — colors, borders, column widths, number formats
- Zero formula errors in the output

Read `references/xlsx-processing.md` for detailed openpyxl and pandas patterns.

### DOCX Output (Word Documents)

**Creating new DOCX from scratch** — use python-docx:
```python
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()
doc.add_heading('Title', level=0)
doc.add_paragraph('Body text here.')
table = doc.add_table(rows=3, cols=3)
doc.save('output.docx')
```

**Editing existing DOCX** — two approaches:
1. **python-docx** for simple edits (replacing text, updating tables, changing styles)
2. **Unpack/edit XML/pack** for complex edits (tracked changes, comments, precise formatting)

**Critical DOCX rules:**
- Set page size explicitly — defaults to A4, use `section.page_width = Inches(8.5)` for US Letter
- Table widths need both column widths and individual cell widths set
- Use `Pt()` for font sizes, `Inches()` for dimensions, `RGBColor()` for colors
- Never insert unicode bullets manually — use proper list styles
- Page breaks must be inside Paragraph elements

Read `references/docx-processing.md` for detailed python-docx patterns and the XML editing workflow.

### CSV Output

Simple — use pandas:
```python
import pandas as pd
df = pd.DataFrame(data)
df.to_csv('output.csv', index=False)
```

## Python Dependencies

Install as needed (the subagent should check and install):
```bash
pip3 install pypdf pdfplumber reportlab pdf2image openpyxl pandas python-docx
```

For PDF-to-image conversion, poppler is also needed:
```bash
brew install poppler  # macOS
```

## Subagent Prompt Template

When spawning the Sonnet subagent, use this structure:

```
You are recreating a document. Here is your task:

TEMPLATE STRUCTURE:
<describe the template layout, fields, sections>

DATA TO USE:
<the user's data, mapped to template fields>

OUTPUT FORMAT: <PDF|XLSX|DOCX|CSV>
OUTPUT PATH: <file path>

INSTRUCTIONS:
1. Create the output file matching the template structure exactly
2. Populate all fields with the provided data
3. Preserve all formatting from the original template
4. <format-specific instructions from above>
5. Save to the output path

SCRIPTS AVAILABLE (run from skill directory):
- scripts/pdf/check_fillable_fields.py
- scripts/pdf/extract_form_field_info.py
- scripts/pdf/extract_form_structure.py
- scripts/pdf/convert_pdf_to_images.py
- scripts/pdf/fill_fillable_fields.py
- scripts/pdf/fill_pdf_form_with_annotations.py
- scripts/pdf/check_bounding_boxes.py
- scripts/xlsx/recalc.py
```

## Reference Files

Read these when you need detailed API patterns for a specific format:
- `references/pdf-processing.md` — PDF creation, extraction, form filling, OCR
- `references/xlsx-processing.md` — Excel creation, editing, formulas, formatting
- `references/docx-processing.md` — Word document creation, editing, tables, styles
