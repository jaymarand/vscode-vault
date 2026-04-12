# HR Document Generator

Web app + Telegram bot for generating Goodwill HR documents from the field.

## What It Does

- **Coaching Forms** — Input employee info + issue, generates filled coaching PDF
- **Warning Records** — Same flow, escalated format
- **Annual Reviews** — Input performance notes + % increase, generates review in original format
- All documents tie back to Ohio Valley Goodwill Way Fundamentals
- Editable preview before download/print
- Generated docs saved to cloud, synced to vault by Claude Code

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Streamlit   │────▶│  Claude API      │────▶│  Generated  │
│  Web App     │     │  (Sonnet)        │     │  DOCX/PDF   │
└─────────────┘     └──────────────────┘     └──────┬──────┘
                                                     │
┌─────────────┐     ┌──────────────────┐            │
│  Telegram    │────▶│  Same backend    │────────────┘
│  Bot         │     │                  │            │
└─────────────┘     └──────────────────┘            ▼
                                              ┌─────────────┐
                                              │  Cloud       │
                                              │  Storage     │
                                              │  (GitHub/    │
                                              │   Vercel)    │
                                              └──────┬──────┘
                                                     │
                                              ┌──────▼──────┐
                                              │  Vault       │
                                              │  /outputs/   │
                                              │  (via sync)  │
                                              └─────────────┘
```

## Stack

- **Frontend:** Streamlit
- **AI:** Claude API (Sonnet) via Anthropic SDK
- **Doc generation:** python-docx, reportlab
- **Bot:** Telegram Bot API
- **Deploy:** Streamlit Cloud or Vercel
- **Storage:** GitHub repo or Vercel Blob
- **Sync:** Claude Code checks for new files on schedule

## Templates

Templates stored in vault at:
`.claude/skills/document-recreator/templates/`

Needed:
- [ ] Coaching form template (reverse-engineer from Michelle Baird example)
- [ ] Warning record template
- [ ] Annual review template

## Fundamentals Integration

The 26 Ohio Valley Goodwill Way Fundamentals are embedded in the app.
AI selects the most relevant fundamental(s) for each situation and weaves
them into the document's "Why Does It Matter?" or equivalent section.

## Vault Sync

Generated documents save to cloud with naming convention:
`YYYY-MM-DD_Firstname-Lastname_type.pdf`

Claude Code runs periodic checks (via /loop or scheduled trigger) to:
1. Check cloud storage for new files
2. Download to `vault/outputs/{coachings|warnings|reviews}/`
3. Update the past-due reviews tracker if a review was completed

## Running

```bash
# Install dependencies
pip install -r requirements.txt

# Run the web app
streamlit run app/streamlit_app.py

# Run the Telegram bot (separate process)
python app/telegram_bot.py
```

Requires `.env.local` in vault root with:
- `ANTHROPIC_API_KEY` — Claude API key
- `TELEGRAM_BOT_TOKEN` — Telegram bot token

## Status

- [x] Build Streamlit app with 3 tabs (coaching, warning, annual review)
- [x] Integrate Claude API for text generation (Sonnet)
- [x] Template-based DOCX generation preserving original formatting
- [x] Editable preview before download
- [x] Goodwill Way Fundamentals integration (all 27)
- [x] Add Telegram bot
- [ ] Deploy to cloud (Streamlit Cloud or Vercel)
- [ ] Set up vault sync
