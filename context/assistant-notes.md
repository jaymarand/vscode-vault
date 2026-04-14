# Assistant Notes

Learned behaviors and context that should persist across machines and sessions.
CLAUDE.md references this file. Update it as things change.

## How to Check Review Status

When asked about past-due reviews, check BOTH:
1. `outputs/reviews/past-due-reviews.md` — the master tracker
2. `outputs/reviews/*.docx` — completed review files

Cross-reference both. If a completed file exists but the tracker doesn't reflect it, update the tracker.

## HR Document Generator

- App lives at `projects/hr-document-generator/`
- 4 tabs: Coaching, Warning, Annual Review, Development Plan
- Templates in `projects/hr-document-generator/app/templates/`
- Reference docs in `.claude/skills/document-recreator/references/`
- Telegram bot: @OVGI_work_Bot (token in .env.local)
- Generated docs auto-save to `outputs/{coachings|warnings|reviews|pdps}/`
- Annual review has TWO parts: Personnel Action Request form + Performance Rating Form
- "Interaction with consumers" trait — always use "Meets expectations." (consumers = people with disabilities Goodwill serves)
- Trait comments must be 11pt font for page spacing
- Goals: exactly 3, position-specific, deadlines ~1 year after review period end
- Woodlawn store was renamed to Tri-County — use Tri-County going forward
- Supervisor for Tri-County (formerly Woodlawn): Holscher, Ciera
- PDP tracker: `outputs/pdps/pdp-tracker.md` — 16 district leadership staff

## Telegram Assistant

- Standalone bot at `projects/telegram-assistant/bot.py`
- Full Claude assistant, not just HR docs
- Loads vault context files as system prompt

## Credentials

All in `.env.local` at vault root (not in git):
- `ANTHROPIC_API_KEY`
- `TELEGRAM_BOT_TOKEN`
