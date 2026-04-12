---
name: gmail
description: Send, draft, read, search, and manage emails via Gmail MCP. Use this skill whenever the user wants to send an email, draft a reply, check their inbox, search for emails, follow up on a thread, or do anything involving email. Also triggers on "email this to," "send a message to," "reply to," "check my email," "find that email from," "draft an email," "follow up with," or any reference to Gmail or email tasks. For cold outreach templates, also reference the cold-email skill.
---

# Gmail

Send, read, search, and manage emails through the Gmail MCP server.

## Setup

The Gmail MCP server must be authenticated before use. If tools aren't available, run the authenticate flow:

1. Call `mcp__claude_ai_Gmail__authenticate` to get an OAuth URL
2. User opens the URL and authorizes
3. Call `mcp__claude_ai_Gmail__complete_authentication` with the callback URL
4. Gmail tools become available

## Core Workflows

### Sending an Email

Before sending, always:
1. Draft the email and show it to the user
2. Wait for approval before sending
3. Never send without explicit confirmation

**Compose from scratch:**
- Ask: who, subject, and what to say (or infer from context)
- Draft using the user's tone (casual internally, factual externally -- see communication rules)
- Present the draft for review
- Send only after approval

**Reply to a thread:**
- Read the original message first for context
- Draft a reply that addresses all points
- Match the tone of the conversation
- Present for review before sending

### Reading & Searching Email

- Search by sender, subject, date range, or keywords
- Summarize long threads into bullet points
- Flag action items and deadlines
- Identify emails that need a response

### Batch Email Processing

When the user says "check my email" or "what needs my attention":

1. Search for recent unread messages
2. Categorize by urgency:
   - **Needs response today** — direct requests, deadlines, boss/team
   - **Needs response this week** — follow-ups, non-urgent asks
   - **FYI only** — newsletters, notifications, CC'd threads
3. Present the summary
4. Offer to draft replies for the urgent ones

## Writing Guidelines

### Internal (Goodwill team)
- Professional but not stiff
- Get to the point fast
- Use the recipient's name
- Keep it short -- 3-5 sentences max for routine items

### External (JPL business, cold outreach)
- No pleasantries or filler
- Factual, simple language
- Lead with value, not introduction
- Reference the cold-email skill for outreach templates

### All Emails
- No emojis
- No "I hope this email finds you well"
- No "just checking in" (say what you actually need)
- Subject lines: short, specific, lowercase-friendly
- One ask per email when possible

## Context Awareness

Before drafting, check:
- `context/team.md` — know who the key people are and their roles
- `context/work.md` — understand both JPL and Goodwill contexts
- `context/current-priorities.md` — align email priorities with current focus

If the email is to someone listed in team.md (Dawn, Mark, Kelly, Michael, Heidi, Lauren, store managers), use the appropriate level of formality for their role.

## Safety Rules

- **Never send without user approval** — always show the draft first
- **Never share sensitive data** — no passwords, financial details, or personal info unless explicitly told to
- **Flag risky sends** — if an email could be misread or seems emotionally charged, say so before sending
- **Confirm recipients** — double-check the "to" field before sending, especially for sensitive topics
