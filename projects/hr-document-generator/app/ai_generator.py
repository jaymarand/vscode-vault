"""Claude API integration for generating HR document content."""

import anthropic
from fundamentals import FUNDAMENTALS, FUNDAMENTALS_LIST


def get_client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key)


SYSTEM_PROMPT = """You are an HR document writer for Ohio Valley Goodwill Industries.
You write professional, clear, and direct HR documents.
Always write in third person. Be specific and factual.
Keep language professional but accessible.
When referencing Goodwill Way Fundamentals, weave them naturally into the narrative —
don't just list them."""


def generate_coaching(
    client: anthropic.Anthropic,
    employee_name: str,
    location: str,
    date: str,
    categories: list[str],
    issue_summary: str,
    manager_name: str = "Jason Cole",
) -> dict:
    """Generate all text fields for a coaching form."""
    prompt = f"""Generate content for a Coaching Session Notes form.

Employee: {employee_name}
Location/Department: {location}
Date: {date}
Categories: {', '.join(categories)}
Manager: {manager_name}

Situation summary from the manager:
{issue_summary}

Here are the Ohio Valley Goodwill Way Fundamentals. Pick the 1-2 most relevant ones and weave them into the "Why Does It Matter?" section:
{FUNDAMENTALS_LIST}

Return your response in this exact format with these section headers:

DESCRIPTION OF BEHAVIOR/ISSUE:
[2-3 sentences describing the observed behavior or issue factually]

EXPECTED BEHAVIOR/PERFORMANCE:
[2-3 sentences describing what is expected going forward, with specific measurable expectations]

WHY DOES IT MATTER:
[2-3 sentences explaining why this matters, naturally incorporating the most relevant Goodwill Way Fundamental(s)]

STEPS EMPLOYEE WILL TAKE TO IMPROVE:
[3-4 specific action steps as comma-separated items]

RESOURCES OR SUPPORT PROVIDED BY MANAGER:
[2-3 specific resources or support items the manager will provide]

TIMELINE FOR IMPROVEMENT:
[One clear timeline statement]

NEXT CHECK-IN DATE:
[A specific date approximately 2 weeks from {date}]

WHAT WILL BE REVIEWED:
[2-3 sentences describing what will be evaluated at follow-up]"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    return _parse_sections(message.content[0].text)


def generate_warning(
    client: anthropic.Anthropic,
    employee_name: str,
    job_title: str,
    department: str,
    date: str,
    violation_type: str,
    issue_summary: str,
) -> dict:
    """Generate content for a written warning."""
    prompt = f"""Generate content for a Written Warning document.

Employee: {employee_name}
Job Title: {job_title}
Department: {department}
Date: {date}
Nature of Violation: {violation_type}

Situation summary from the manager:
{issue_summary}

Here are the Ohio Valley Goodwill Way Fundamentals for context:
{FUNDAMENTALS_LIST}

Return your response in this exact format:

NATURE OF VIOLATION:
[One line stating the violation group and rule, e.g. "Group II Rule – Failure to Meet Job Performance Expectations"]

ADDITIONAL COMMENTS:
[3-5 paragraphs providing detailed narrative of the issues. Be specific and factual.
Include what has been observed, any prior coaching or direction given, any partial improvements noted,
and the specific documented concerns. End with the baseline expectations going forward.]

REQUIRED IMPROVEMENTS:
[5-8 bullet points of specific required improvements, each starting with a verb]

REVIEW PERIOD:
[State the review period length, e.g. "30-Day Review Period"]"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    return _parse_sections(message.content[0].text)


def generate_annual_review(
    client: anthropic.Anthropic,
    employee_name: str,
    job_title: str,
    department: str,
    date_of_hire: str,
    period_from: str,
    period_to: str,
    current_pay: str,
    percent_increase: str,
    performance_notes: str,
) -> dict:
    """Generate content for an annual performance review."""
    new_pay = ""
    try:
        rate = float(current_pay)
        pct = float(percent_increase.strip("%"))
        new_pay = f"${rate * (1 + pct / 100):.2f}"
    except (ValueError, TypeError):
        pass

    prompt = f"""Generate content for an Annual Performance Review.

Employee: {employee_name}
Job Title: {job_title}
Department: {department}
Date of Hire: {date_of_hire}
Review Period: {period_from} to {period_to}
Current Pay Rate: ${current_pay}
Percent Increase: {percent_increase}%
New Pay Rate: {new_pay}

Manager's performance notes:
{performance_notes}

The performance traits to rate are:
Attendance/Dependability, Communication, Decision Making, Flexibility/Adaptability,
Housekeeping/Safety, Job Knowledge, Morale, Dress/Personal Appearance,
Personal Interaction/Customer Service, Task Completion, Work Habits, Work Quality,
EEOC Accountability, Interaction with Consumers

Rating scale: E (Excellent), AB (Above Average), G (Good), F (Fair), U (Unsatisfactory)

Here are the Ohio Valley Goodwill Way Fundamentals for context:
{FUNDAMENTALS_LIST}

Return your response in this exact format:

TRAIT RATINGS:
[One line per trait in format: Trait Name|Rating|Brief comment]
Example: Attendance/Dependability|AB|Demonstrates reliability through excellent attendance.
IMPORTANT: For the "Interaction with consumers" trait, always use exactly this comment: "Meets expectations."
Do not elaborate on this trait. Goodwill serves people with disabilities — "consumers" is intentional, not a typo.

SUPERVISOR NARRATIVE:
[2-3 paragraphs summarizing accomplishments, areas for growth, and overall assessment.
Naturally incorporate relevant Goodwill Way Fundamentals.]

GOALS:
[Exactly 3 numbered goals for the upcoming year. Each goal must be specific to the employee's
role as {job_title}, with a measurable target and deadline. Focus on practical skills and
responsibilities relevant to their day-to-day position.
All goal deadlines must fall within approximately one year after {period_to} (the end of the
review period). Use specific months, not vague timeframes.]"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    result = _parse_sections(message.content[0].text)

    # Parse trait ratings into structured data
    if "TRAIT RATINGS" in result:
        traits = []
        for line in result["TRAIT RATINGS"].strip().split("\n"):
            line = line.strip()
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 3:
                    traits.append({
                        "trait": parts[0].strip(),
                        "rating": parts[1].strip(),
                        "comment": parts[2].strip(),
                    })
        result["trait_ratings_parsed"] = traits

    result["new_pay"] = new_pay
    return result


def generate_pdp(
    client: anthropic.Anthropic,
    employee_name: str,
    position: str,
    location: str,
    ultimate_goal: str,
    notes: str,
) -> dict:
    """Generate a Professional Development Plan with 3 goals and action steps."""
    prompt = f"""Generate a Professional Development Plan for a Goodwill employee.

Employee: {employee_name}
Position: {position}
Work Location: {location}
Their ultimate goal: {ultimate_goal}

Manager's notes about this employee's development needs:
{notes}

The PDP has 3 goals. Each goal should be a different type:
- Personal/Interpersonal Growth (EI, self-awareness, communication, relationships)
- Technical/Job Skills (role-specific capabilities, processes, systems)
- Leadership Capabilities (leading others, managing, influencing)
- Career Planning (advancement, new roles, long-term trajectory)

Goals must be SMART: Specific, Measurable, Achievable, Relevant, Time-bound.

The "My Why" for each goal must answer: Why does this matter to YOU? What problem does it solve?
How does it impact your team, store, or OVGI's mission? Strong whys are personal and specific.

Each goal needs 2 concrete action steps. Action steps are the HOW — specific, concrete activities.

Support partners can be: EAP, HR, L&D, OC (Opportunity Center), Wellness, or a specific person.

Return your response in this exact format:

ULTIMATE GOAL:
[One sentence restatement of their ultimate career/development goal]

GOAL 1:
[Clear, specific SMART goal statement]

GOAL 1 TYPE:
[Exactly one of: Personal/Interpersonal Growth, Technical/Job Skills, Leadership Capabilities, Career Planning]

GOAL 1 WHY:
[2-3 sentences — personal, specific, explains impact on team/store/mission]

GOAL 1 TIMEFRAME:
[Exactly one of: 1 month, 3 months, 6 months, 1 year]

GOAL 2:
[Clear, specific SMART goal statement]

GOAL 2 TYPE:
[Type]

GOAL 2 WHY:
[2-3 sentences]

GOAL 2 TIMEFRAME:
[Timeframe]

GOAL 3:
[Clear, specific SMART goal statement]

GOAL 3 TYPE:
[Type]

GOAL 3 WHY:
[2-3 sentences]

GOAL 3 TIMEFRAME:
[Timeframe]

ACTION 1:
[Concrete action step for goal 1]

ACTION 1 GOALS:
[Comma-separated goal numbers this supports, e.g. "1" or "1,2"]

ACTION 1 SUPPORT:
[Support partner — a person role or department]

ACTION 1 RESOURCE:
[One of: EAP, HR, L&D, OC, Wellness, or Other]

ACTION 2:
[Concrete action step for goal 1]

ACTION 2 GOALS:
[Goal numbers]

ACTION 2 SUPPORT:
[Support partner]

ACTION 2 RESOURCE:
[Resource]

ACTION 3:
[Concrete action step for goal 2]

ACTION 3 GOALS:
[Goal numbers]

ACTION 3 SUPPORT:
[Support partner]

ACTION 3 RESOURCE:
[Resource]

ACTION 4:
[Concrete action step for goal 2]

ACTION 4 GOALS:
[Goal numbers]

ACTION 4 SUPPORT:
[Support partner]

ACTION 4 RESOURCE:
[Resource]

ACTION 5:
[Concrete action step for goal 3]

ACTION 5 GOALS:
[Goal numbers]

ACTION 5 SUPPORT:
[Support partner]

ACTION 5 RESOURCE:
[Resource]

ACTION 6:
[Concrete action step for goal 3]

ACTION 6 GOALS:
[Goal numbers]

ACTION 6 SUPPORT:
[Support partner]

ACTION 6 RESOURCE:
[Resource]"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    result = _parse_sections(message.content[0].text)

    # Structure goals
    goals = []
    for i in range(1, 4):
        goals.append({
            "goal": result.get(f"GOAL {i}", ""),
            "type": result.get(f"GOAL {i} TYPE", ""),
            "why": result.get(f"GOAL {i} WHY", ""),
            "timeframe": result.get(f"GOAL {i} TIMEFRAME", ""),
        })
    result["goals_parsed"] = goals

    # Structure actions
    actions = []
    for i in range(1, 7):
        actions.append({
            "action": result.get(f"ACTION {i}", ""),
            "goals": result.get(f"ACTION {i} GOALS", ""),
            "support": result.get(f"ACTION {i} SUPPORT", ""),
            "resource": result.get(f"ACTION {i} RESOURCE", ""),
        })
    result["actions_parsed"] = actions

    return result


def _parse_sections(text: str) -> dict:
    """Parse AI response into sections by header."""
    sections = {}
    current_key = None
    current_lines = []

    for line in text.split("\n"):
        stripped = line.strip()
        # Check if this is a section header (ALL CAPS followed by colon)
        if stripped.endswith(":") and stripped[:-1].replace(" ", "").replace("/", "").replace("'", "").replace("-", "").isupper() and len(stripped) > 3:
            if current_key:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = stripped[:-1].strip()
            current_lines = []
        elif current_key:
            current_lines.append(line)

    if current_key:
        sections[current_key] = "\n".join(current_lines).strip()

    return sections
