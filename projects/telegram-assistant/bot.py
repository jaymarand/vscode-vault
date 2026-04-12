"""Jason's main AI assistant — Telegram interface to Claude.

This is a direct line to Claude from your phone. Full vault context,
conversation memory, and the ability to check files, draft content,
and answer questions about your stores, team, and business.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
import anthropic
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Load env from vault root
VAULT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(VAULT_ROOT / ".env.local")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Max conversation history per user (message pairs)
MAX_HISTORY = 20


# ---------------------------------------------------------------------------
# Context loader — reads vault files for system prompt
# ---------------------------------------------------------------------------

def load_vault_context() -> str:
    """Read key vault files to build the system prompt context."""
    context_parts = []

    context_files = [
        ("context/me.md", "About Jason"),
        ("context/work.md", "Business & Work"),
        ("context/team.md", "Team"),
        ("context/current-priorities.md", "Current Priorities"),
        ("context/goals.md", "Goals"),
    ]

    for filepath, label in context_files:
        full_path = VAULT_ROOT / filepath
        if full_path.exists():
            content = full_path.read_text().strip()
            context_parts.append(f"## {label}\n{content}")

    # Check for past-due reviews
    reviews_path = VAULT_ROOT / "outputs" / "reviews" / "past-due-reviews.md"
    if reviews_path.exists():
        context_parts.append(f"## Past-Due Reviews Tracker\n{reviews_path.read_text().strip()}")

    return "\n\n---\n\n".join(context_parts)


def build_system_prompt() -> str:
    """Build the full system prompt with vault context."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    vault_context = load_vault_context()

    return f"""You are Jason Cole's executive assistant. You communicate via Telegram,
so keep responses concise and mobile-friendly.

Today is {today}.

## How to communicate
- Short paragraphs, bullet points when listing things
- No fluff or preamble — lead with the answer
- Casual tone with Jason, professional when drafting external content
- Use emoji sparingly and only when natural

## What you can help with
- Goodwill operations: store questions, team info, review status, drafting emails
- JPL business: planning, strategy, technical questions
- Quick lookups from vault context below
- Drafting messages, emails, responses
- Thinking through decisions
- Anything Jason would ask his assistant

## Vault Context
{vault_context}

## Important notes
- Jason is District Director of East District at Ohio Valley Goodwill
- His boss is Dawn Corley (VP of Retail)
- He's building JPL (automated AI businesses) on the side — this is his top priority
- He's moving back to California in September 2026
- When he asks about reviews, reference the past-due reviews tracker
- Keep responses under 4000 characters (Telegram limit)"""


# ---------------------------------------------------------------------------
# Conversation memory (in-process, per chat)
# ---------------------------------------------------------------------------

conversations: dict[int, list[dict]] = {}


def get_history(chat_id: int) -> list[dict]:
    """Get conversation history for a chat."""
    if chat_id not in conversations:
        conversations[chat_id] = []
    return conversations[chat_id]


def add_to_history(chat_id: int, role: str, content: str):
    """Add a message to conversation history."""
    history = get_history(chat_id)
    history.append({"role": role, "content": content})
    # Trim to max history
    if len(history) > MAX_HISTORY * 2:
        conversations[chat_id] = history[-(MAX_HISTORY * 2):]


# ---------------------------------------------------------------------------
# Claude API
# ---------------------------------------------------------------------------

def get_claude_response(chat_id: int, user_message: str) -> str:
    """Send message to Claude with conversation history and vault context."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "API key not configured. Set ANTHROPIC_API_KEY in .env.local"

    client = anthropic.Anthropic(api_key=api_key)

    # Reload system prompt each time to get fresh vault data
    system_prompt = build_system_prompt()

    # Build messages with history
    add_to_history(chat_id, "user", user_message)
    messages = get_history(chat_id)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt,
            messages=messages,
        )
        reply = response.content[0].text
        add_to_history(chat_id, "assistant", reply)
        return reply
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return f"Error talking to Claude: {e}"


# ---------------------------------------------------------------------------
# Telegram handlers
# ---------------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(
        "Hey Jason. I'm your assistant — ask me anything.\n\n"
        "I have your vault context loaded (team, priorities, reviews, etc).\n\n"
        "Commands:\n"
        "/clear — reset conversation\n"
        "/reviews — past-due review status\n"
        "/priorities — current priorities"
    )


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear conversation history."""
    chat_id = update.effective_chat.id
    conversations.pop(chat_id, None)
    await update.message.reply_text("Conversation cleared.")


async def reviews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick review status."""
    reviews_path = VAULT_ROOT / "outputs" / "reviews" / "past-due-reviews.md"
    if reviews_path.exists():
        content = reviews_path.read_text()
        # Count remaining (not Done, not Termed, not Submitted)
        lines = content.split("\n")
        remaining = []
        for line in lines:
            if "|" in line and "~~" not in line and "Submitted" not in line:
                cells = [c.strip() for c in line.split("|")]
                if len(cells) >= 4 and cells[1] and cells[1] not in ("Employee", "Store", "-------"):
                    try:
                        int(cells[4])  # days past due is a number
                        remaining.append(f"• {cells[1]} — {cells[2]} — {cells[4]} days")
                    except (ValueError, IndexError):
                        pass

        count = len(remaining)
        msg = f"**{count} reviews remaining:**\n\n" + "\n".join(remaining)
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text("No review tracker found.")


async def priorities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current priorities."""
    path = VAULT_ROOT / "context" / "current-priorities.md"
    if path.exists():
        content = path.read_text().strip()
        await update.message.reply_text(content)
    else:
        await update.message.reply_text("No priorities file found.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any text message — send to Claude."""
    chat_id = update.effective_chat.id
    user_message = update.message.text

    # Show typing indicator
    await update.effective_chat.send_action("typing")

    reply = get_claude_response(chat_id, user_message)

    # Telegram has a 4096 char limit — split if needed
    if len(reply) <= 4096:
        await update.message.reply_text(reply)
    else:
        chunks = [reply[i:i+4096] for i in range(0, len(reply), 4096)]
        for chunk in chunks:
            await update.message.reply_text(chunk)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("Set TELEGRAM_BOT_TOKEN in .env.local")
        sys.exit(1)

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("reviews", reviews))
    app.add_handler(CommandHandler("priorities", priorities))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Assistant bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
