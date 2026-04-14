---
name: store-review-prep
description: Generate a pre-filled Goodwill store review Excel file for any East District store. Use this skill when Jason asks to generate a store review, prep a store visit form, fill out a store review, or create a review for any of his stores (Lebanon, Beechmont, Tri-County, Loveland, Fairfield, Deerfield, ShopGoodwill). Also triggers when he says "run a store review for [store]" or "prep the review form."
---

# Store Review Prep

Generates a pre-filled store review Excel file by extracting metrics from uploaded data reports and using AI to write the General Store Comments and Three Most Important Priorities with SMART action plans.

## Workflow

### Step 1 — Gather inputs

Ask the user for:
1. **Store name** (if not already provided)
2. **Visit date** and **previous evaluation date**
3. **Daily Sales Report** (Retail Metrics by District.xlsx) — upload
4. **Rack Units Report** (weekly, optional but strongly recommended) — upload
5. **Turnover Report** (monthly, optional) — upload
6. **Manual observation fields** — collect via questions:
   - Labor % to Budget (e.g. 0.27 = 27%)
   - Donation Growth % to LY
   - # of Open Positions
   - Ecommerce % +/- to Budget
   - Number of Ecommerce Totes sent MTD
   - Is truck loaded correctly? (Yes/No)
   - Huddles — Complete or Incomplete? (and # days missing if incomplete)
   - # Rolling Racks checked / # items sent back
   - # Totes checked / # tote items sent back
   - Hang Count Variance (decimal, e.g. -0.15)
   - Tote Count Variance (decimal)
   - Names of hourly employees had 5-min conversation with
   - New hires met (Yes/No) / Number of new hires
   - Merchandising Yes/No fields: Wares Shelves Full, Racks Full, Shoe Racks Full, End Caps Full
   - Store Cleanliness Yes/No: Parking Lot, Donation Area, Windows/Entry, Cash Wraps, Floor/Racks, Wares/Shelves, Fitting Rooms, Production Room, Offices
   - Pull/Rotation Validation Yes/No: Women's Rack, Men's Rack, Kid's Rack, Wares, Shoes, Books, E&M
   - Error Rate Rack: Total # items checked, # Wrong Price, # Defective, # Wrong Category/Size
   - Error Rate Containers: Total # containers checked, Not Labeled, Labeled as Salvage but Raw, Labeled as Raw but Salvage, Labeled as Soft but Hard, Labeled as Hard but Soft
   - Any carry-over priorities from the last visit? (Incomplete/In Process)

You can ask these all at once or accept partial data — generate the review with whatever is available and leave blanks for the rest.

### Step 2 — Extract metrics from uploaded files

Run the extraction script:
```
cd c:\Users\jason\vscode-vault
python .claude/skills/store-review-prep/scripts/extract_metrics.py \
  --store "<store_name>" \
  --sales "<path_to_sales_report>" \
  --rack_units "<path_to_rack_units_report>" \
  --turnover "<path_to_turnover_report>"
```

This outputs a JSON of extracted metrics for the store.

### Step 3 — Generate AI content

Use the extracted metrics + manual inputs to generate:
1. **General Store Comments** (~300-400 words)
2. **Three Most Important Priorities** (each with Opportunity statement + SMART Action Plan)

Read `references/generation-patterns.md` for the exact style and structure to follow.
Read `references/store-roster.md` for manager names — always use them in SMART goals.

### Step 4 — Build the Excel file

Run the fill script:
```
cd c:\Users\jason\vscode-vault
python .claude/skills/store-review-prep/scripts/fill_review.py \
  --store "<store_name>" \
  --visit_date "<YYYY-MM-DD>" \
  --prev_date "<YYYY-MM-DD>" \
  --metrics_json "<path_to_metrics.json>" \
  --manual_json "<path_to_manual_inputs.json>" \
  --comments "<escaped_comments_text>" \
  --priorities_json "<path_to_priorities.json>" \
  --output "outputs/store-reviews/<YYYY-MM-DD>_<store>_store-review.xlsx"
```

### Step 5 — Confirm output

Tell the user the file was saved to `outputs/store-reviews/` and is ready to open, review, and finalize. Note any fields left blank that need manual entry.

## Notes

- The template uses merged cells extensively — the fill script handles this correctly using cell coordinate mapping, not openpyxl's value_only mode.
- Formulas in the error rate section (rows 14-17, 22-27) are preserved — only input counts are written, not the calculated % columns.
- Always preserve existing Excel formatting — load the template and write into it, never create from scratch.
- Output goes to `outputs/store-reviews/` at vault root (not inside the project folder).
