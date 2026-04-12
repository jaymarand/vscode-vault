"""Telegram bot for HR Document Generator.

Allows Jason to generate coaching forms, warnings, and reviews
from his phone via conversational prompts.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

sys.path.insert(0, str(Path(__file__).parent))

from ai_generator import get_client, generate_coaching, generate_warning, generate_annual_review
from doc_builder import build_coaching_docx, build_warning_docx, build_annual_review_docx

load_dotenv(Path(__file__).parent.parent.parent.parent / ".env.local")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
CHOOSE_TYPE, COLLECT_INFO, CONFIRM = range(3)


def get_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        key = os.environ.get("claude_api_key", "")
    return key


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Coaching", callback_data="coaching")],
        [InlineKeyboardButton("Warning", callback_data="warning")],
        [InlineKeyboardButton("Annual Review", callback_data="review")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "What type of HR document do you need?",
        reply_markup=reply_markup,
    )
    return CHOOSE_TYPE


async def choose_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    doc_type = query.data
    context.user_data["doc_type"] = doc_type

    prompts = {
        "coaching": (
            "Send me the coaching details in this format:\n\n"
            "Employee: [name]\n"
            "Location: [store/dept]\n"
            "Category: [Performance/Policy/Attendance]\n"
            "Issue: [describe what happened]"
        ),
        "warning": (
            "Send me the warning details in this format:\n\n"
            "Employee: [name]\n"
            "Title: [job title]\n"
            "Department: [dept]\n"
            "Issue: [describe the situation in detail — "
            "include prior coaching, improvements seen, remaining concerns]"
        ),
        "review": (
            "Send me the review details in this format:\n\n"
            "Employee: [name]\n"
            "Title: [job title]\n"
            "Department: [dept]\n"
            "Hire Date: [MM/DD/YYYY]\n"
            "Period: [MM/DD/YYYY to MM/DD/YYYY]\n"
            "Pay: [current rate]\n"
            "Increase: [percent]\n"
            "Notes: [performance observations]"
        ),
    }

    await query.edit_message_text(prompts[doc_type])
    return COLLECT_INFO


def _parse_input(text: str) -> dict:
    """Parse key: value lines from user input."""
    data = {}
    current_key = None
    current_val = []

    for line in text.split("\n"):
        if ":" in line:
            # Check if this looks like a key:value pair
            parts = line.split(":", 1)
            key = parts[0].strip().lower()
            if len(key) < 30:  # Likely a label, not part of content
                if current_key:
                    data[current_key] = "\n".join(current_val).strip()
                current_key = key
                current_val = [parts[1].strip()]
                continue
        if current_key:
            current_val.append(line)

    if current_key:
        data[current_key] = "\n".join(current_val).strip()

    return data


async def collect_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    doc_type = context.user_data.get("doc_type")
    data = _parse_input(text)
    context.user_data["input_data"] = data

    api_key = get_api_key()
    if not api_key:
        await update.message.reply_text("API key not configured. Set ANTHROPIC_API_KEY in .env.local")
        return ConversationHandler.END

    await update.message.reply_text("Generating document... this takes about 10 seconds.")

    client = get_client(api_key)
    today = datetime.now().strftime("%m/%d/%Y")

    try:
        if doc_type == "coaching":
            employee = data.get("employee", "Unknown")
            location = data.get("location", "")
            category_str = data.get("category", "Performance Improvement")
            categories = [c.strip() for c in category_str.split(",")]
            issue = data.get("issue", text)

            ai = generate_coaching(
                client=client,
                employee_name=employee,
                location=location,
                date=today,
                categories=categories,
                issue_summary=issue,
            )

            docx_bytes = build_coaching_docx(
                employee_name=employee,
                date=today,
                location=location,
                categories=categories,
                ai_content=ai,
            )
            filename = f"{datetime.now().strftime('%Y-%m-%d')}_{employee.replace(' ', '-')}_coaching.docx"

        elif doc_type == "warning":
            employee = data.get("employee", "Unknown")
            title = data.get("title", "")
            dept = data.get("department", "")
            issue = data.get("issue", text)

            ai = generate_warning(
                client=client,
                employee_name=employee,
                job_title=title,
                department=dept,
                date=today,
                violation_type="Group II Rule – Failure to Meet Job Performance Expectations",
                issue_summary=issue,
            )

            docx_bytes = build_warning_docx(
                employee_name=employee,
                job_title=title,
                department=dept,
                date=today,
                ai_content=ai,
            )
            filename = f"{datetime.now().strftime('%Y-%m-%d')}_{employee.replace(' ', '-')}_warning.docx"

        elif doc_type == "review":
            employee = data.get("employee", "Unknown")
            title = data.get("title", "")
            dept = data.get("department", "")
            hire = data.get("hire date", "")
            period = data.get("period", "")
            period_parts = period.split(" to ") if " to " in period else [period, ""]
            pay = data.get("pay", "0")
            increase = data.get("increase", "3.0").strip("%")
            notes = data.get("notes", text)

            ai = generate_annual_review(
                client=client,
                employee_name=employee,
                job_title=title,
                department=dept,
                date_of_hire=hire,
                period_from=period_parts[0].strip(),
                period_to=period_parts[1].strip() if len(period_parts) > 1 else "",
                current_pay=pay,
                percent_increase=increase,
                performance_notes=notes,
            )

            docx_bytes = build_annual_review_docx(
                employee_name=employee,
                job_title=title,
                department=dept,
                date_of_hire=hire,
                period_from=period_parts[0].strip(),
                period_to=period_parts[1].strip() if len(period_parts) > 1 else "",
                current_pay=pay,
                percent_increase=increase,
                new_pay=ai.get("new_pay", ""),
                ai_content=ai,
            )
            filename = f"{datetime.now().strftime('%Y-%m-%d')}_{employee.replace(' ', '-')}_annual-review.docx"

        else:
            await update.message.reply_text("Unknown document type.")
            return ConversationHandler.END

        await update.message.reply_document(
            document=docx_bytes,
            filename=filename,
            caption=f"Here's your {doc_type} document for {data.get('employee', 'the employee')}. Review before printing.",
        )

    except Exception as e:
        logger.error(f"Error generating document: {e}")
        await update.message.reply_text(f"Error generating document: {e}")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("Set TELEGRAM_BOT_TOKEN in .env.local")
        sys.exit(1)

    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_TYPE: [CallbackQueryHandler(choose_type)],
            COLLECT_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, collect_info)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    # Also handle direct messages without /start
    async def direct_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await start(update, context)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, direct_message))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
