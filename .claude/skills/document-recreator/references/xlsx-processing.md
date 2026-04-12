# XLSX Processing Reference

## Table of Contents
1. [Reading with pandas](#reading)
2. [Creating with openpyxl](#creating)
3. [Editing existing files](#editing)
4. [Formulas — always use them](#formulas)
5. [Formatting standards](#formatting)
6. [Recalculation](#recalc)

## Reading with pandas <a id="reading"></a>

```python
import pandas as pd

df = pd.read_excel('file.xlsx')                    # First sheet
all_sheets = pd.read_excel('file.xlsx', sheet_name=None)  # All sheets as dict
df = pd.read_excel('file.xlsx', dtype={'id': str})  # Specify types
df = pd.read_excel('file.xlsx', usecols=['A', 'C']) # Specific columns
```

## Creating with openpyxl <a id="creating"></a>

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

wb = Workbook()
ws = wb.active
ws.title = "Report"

# Add data
ws['A1'] = 'Header'
ws.append(['Row', 'of', 'data'])

# Formatting
ws['A1'].font = Font(name='Arial', bold=True, size=14, color='FFFFFF')
ws['A1'].fill = PatternFill('solid', fgColor='4472C4')
ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
ws['A1'].border = Border(
    bottom=Side(style='thin', color='000000')
)

# Column width and row height
ws.column_dimensions['A'].width = 20
ws.row_dimensions[1].height = 30

# Merge cells
ws.merge_cells('A1:D1')

wb.save('output.xlsx')
```

## Editing existing files <a id="editing"></a>

```python
from openpyxl import load_workbook

wb = load_workbook('existing.xlsx')
ws = wb.active  # or wb['SheetName']

# Modify
ws['A1'] = 'New Value'
ws.insert_rows(2)
ws.delete_cols(3)

# Add sheet
new_ws = wb.create_sheet('NewSheet')

wb.save('modified.xlsx')
```

**Warning:** Opening with `data_only=True` and saving replaces formulas with values permanently.

## Formulas <a id="formulas"></a>

Use Excel formulas instead of calculating in Python:

```python
# Correct
ws['B10'] = '=SUM(B2:B9)'
ws['C5'] = '=(C4-C2)/C2'
ws['D20'] = '=AVERAGE(D2:D19)'

# Wrong — hardcoded calculation
total = sum(values)
ws['B10'] = total  # Don't do this
```

## Formatting standards <a id="formatting"></a>

### Professional defaults
- Font: Arial or Times New Roman
- Match template formatting exactly when recreating

### Financial model color coding
- Blue text (0,0,255): Hardcoded inputs
- Black text (0,0,0): Formulas
- Green text (0,128,0): Cross-sheet links
- Red text (255,0,0): External links
- Yellow background (255,255,0): Key assumptions

### Number formats
- Currency: `$#,##0`
- Percentages: `0.0%`
- Negatives: parentheses `(123)` not `-123`
- Years: format as text `"2024"` not `2,024`

```python
from openpyxl.styles.numbers import FORMAT_CURRENCY_USD_SIMPLE
ws['A1'].number_format = '$#,##0'
ws['B1'].number_format = '0.0%'
```

## Recalculation <a id="recalc"></a>

After creating or editing files with formulas:

```bash
python3 scripts/xlsx/recalc.py output.xlsx [timeout_seconds]
```

Returns JSON:
```json
{
  "status": "success",
  "total_errors": 0,
  "total_formulas": 42
}
```

If `status` is `errors_found`, check `error_summary` for locations and fix them.

Requires LibreOffice installed (`brew install --cask libreoffice` on macOS).
