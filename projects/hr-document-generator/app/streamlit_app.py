"""HR Document Generator — Streamlit App.

Web UI for generating Goodwill HR documents (coachings, warnings, annual reviews)
using Claude AI and the Ohio Valley Goodwill Way Fundamentals.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Add app dir to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ai_generator import get_client, generate_coaching, generate_warning, generate_annual_review, generate_pdp
from doc_builder import build_coaching_docx, build_warning_docx, build_annual_review_docx, build_pdp_docx
from review_parser import parse_review_docx

# Load env
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env.local")

# Vault outputs directory — save to vault root, not project subfolder
VAULT_OUTPUTS = Path(__file__).parent.parent.parent.parent / "outputs"
# Also handle if running from project dir directly
if not VAULT_OUTPUTS.parent.exists():
    VAULT_OUTPUTS = Path(__file__).parent.parent / "outputs"


def _archive(docx_bytes: bytes, filename: str, doc_type: str):
    """Save generated doc to vault outputs folder."""
    folder = VAULT_OUTPUTS / doc_type
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / filename
    path.write_bytes(docx_bytes)
    return path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="HR Document Generator",
    page_icon="📋",
    layout="wide",
)

def _parse_date_str(date_str: str) -> datetime:
    """Parse a date string like MM/DD/YYYY into a datetime."""
    for fmt in ("%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return datetime.now()


EAST_DISTRICT_LOCATIONS = [
    "Tri-County",
    "Fairfield",
    "Hamilton",
    "Middletown",
    "Oxford",
    "Woodlawn",
    "ShopGoodwill",
    "Other",
]


def get_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        # Try alternate env var name from .env.local
        raw = os.environ.get("claude_api_key", "")
        if raw:
            key = raw
    return key


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("HR Document Generator")
    st.caption("Ohio Valley Goodwill Industries")
    st.divider()

    api_key = get_api_key()
    if not api_key:
        api_key = st.text_input("Anthropic API Key", type="password")
    else:
        st.success("API key loaded")

    manager_name = st.text_input("Manager Name", value="Jason Cole")
    st.divider()
    st.caption("Built for East District operations")


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_coaching, tab_warning, tab_review, tab_pdp = st.tabs([
    "Coaching Session",
    "Written Warning",
    "Annual Review",
    "Development Plan",
])

# ---------------------------------------------------------------------------
# Tab 1: Coaching
# ---------------------------------------------------------------------------

with tab_coaching:
    st.header("Coaching Session Notes")

    col1, col2 = st.columns(2)
    with col1:
        c_employee = st.text_input("Employee Name", key="c_emp")
        c_location = st.selectbox("Location/Department", EAST_DISTRICT_LOCATIONS, key="c_loc")
        if c_location == "Other":
            c_location = st.text_input("Specify location", key="c_loc_other")
    with col2:
        c_date = st.date_input("Date of Coaching", value=datetime.now(), key="c_date")
        c_categories = st.multiselect(
            "Purpose of Coaching",
            ["Performance Improvement", "Policy Violation", "Attendance", "Other"],
            key="c_cats",
        )

    c_summary = st.text_area(
        "Describe the situation (your notes — AI will expand this)",
        height=150,
        key="c_summary",
        placeholder="e.g., Michelle and team haven't been filling out the production tracker daily...",
    )

    if st.button("Generate Coaching Form", type="primary", key="c_gen"):
        if not api_key:
            st.error("Enter your Anthropic API key in the sidebar.")
        elif not c_employee or not c_summary:
            st.error("Fill in employee name and situation summary.")
        else:
            with st.spinner("Generating coaching document..."):
                client = get_client(api_key)
                ai = generate_coaching(
                    client=client,
                    employee_name=c_employee,
                    location=c_location,
                    date=c_date.strftime("%m/%d/%Y"),
                    categories=c_categories,
                    issue_summary=c_summary,
                    manager_name=manager_name,
                )
                st.session_state["c_ai"] = ai

    if "c_ai" in st.session_state:
        ai = st.session_state["c_ai"]
        st.divider()
        st.subheader("Preview & Edit")

        ai["DESCRIPTION OF BEHAVIOR/ISSUE"] = st.text_area(
            "Description of Behavior/Issue",
            value=ai.get("DESCRIPTION OF BEHAVIOR/ISSUE", ""),
            height=100,
            key="c_edit_desc",
        )
        ai["EXPECTED BEHAVIOR/PERFORMANCE"] = st.text_area(
            "Expected Behavior/Performance",
            value=ai.get("EXPECTED BEHAVIOR/PERFORMANCE", ""),
            height=100,
            key="c_edit_exp",
        )
        ai["WHY DOES IT MATTER"] = st.text_area(
            "Why Does It Matter?",
            value=ai.get("WHY DOES IT MATTER", ""),
            height=100,
            key="c_edit_why",
        )
        ai["STEPS EMPLOYEE WILL TAKE TO IMPROVE"] = st.text_area(
            "Steps to Improve",
            value=ai.get("STEPS EMPLOYEE WILL TAKE TO IMPROVE", ""),
            height=100,
            key="c_edit_steps",
        )
        ai["RESOURCES OR SUPPORT PROVIDED BY MANAGER"] = st.text_area(
            "Resources/Support",
            value=ai.get("RESOURCES OR SUPPORT PROVIDED BY MANAGER", ""),
            height=80,
            key="c_edit_res",
        )
        ai["TIMELINE FOR IMPROVEMENT"] = st.text_input(
            "Timeline",
            value=ai.get("TIMELINE FOR IMPROVEMENT", ""),
            key="c_edit_time",
        )
        ai["NEXT CHECK-IN DATE"] = st.text_input(
            "Next Check-In Date",
            value=ai.get("NEXT CHECK-IN DATE", ""),
            key="c_edit_checkin",
        )
        ai["WHAT WILL BE REVIEWED"] = st.text_area(
            "What Will Be Reviewed",
            value=ai.get("WHAT WILL BE REVIEWED", ""),
            height=80,
            key="c_edit_review",
        )

        st.divider()
        if st.button("Download DOCX", key="c_download"):
            docx_bytes = build_coaching_docx(
                employee_name=c_employee,
                date=c_date.strftime("%m/%d/%Y"),
                location=c_location,
                categories=c_categories,
                ai_content=ai,
                manager_name=manager_name,
            )
            filename = f"{c_date.strftime('%Y-%m-%d')}_{c_employee.replace(' ', '-')}_coaching.docx"
            saved = _archive(docx_bytes, filename, "coachings")
            st.caption(f"Saved to `{saved}`")
            st.download_button(
                label="Download Coaching Form",
                data=docx_bytes,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="c_dl_btn",
            )


# ---------------------------------------------------------------------------
# Tab 2: Written Warning
# ---------------------------------------------------------------------------

with tab_warning:
    st.header("Written Warning")

    col1, col2 = st.columns(2)
    with col1:
        w_employee = st.text_input("Employee Name", key="w_emp")
        w_department = st.selectbox("Department", EAST_DISTRICT_LOCATIONS, key="w_dept")
        if w_department == "Other":
            w_department = st.text_input("Specify department", key="w_dept_other")
    with col2:
        w_title = st.text_input("Job Title", key="w_title")
        w_date = st.date_input("Date", value=datetime.now(), key="w_date")

    w_violation = st.selectbox(
        "Violation Type",
        [
            "Group I Rule – Minor Policy Violation",
            "Group II Rule – Failure to Meet Job Performance Expectations",
            "Group II Rule – Failure to Follow Directives",
            "Group III Rule – Serious Misconduct",
            "Other",
        ],
        key="w_viol",
    )
    if w_violation == "Other":
        w_violation = st.text_input("Specify violation", key="w_viol_other")

    w_summary = st.text_area(
        "Describe the situation in detail (AI will structure this into a formal warning)",
        height=200,
        key="w_summary",
        placeholder="Include: what happened, prior coaching/direction given, any improvements seen, remaining concerns...",
    )

    if st.button("Generate Warning", type="primary", key="w_gen"):
        if not api_key:
            st.error("Enter your Anthropic API key in the sidebar.")
        elif not w_employee or not w_summary:
            st.error("Fill in employee name and situation summary.")
        else:
            with st.spinner("Generating warning document..."):
                client = get_client(api_key)
                ai = generate_warning(
                    client=client,
                    employee_name=w_employee,
                    job_title=w_title,
                    department=w_department,
                    date=w_date.strftime("%m/%d/%Y"),
                    violation_type=w_violation,
                    issue_summary=w_summary,
                )
                st.session_state["w_ai"] = ai

    if "w_ai" in st.session_state:
        ai = st.session_state["w_ai"]
        st.divider()
        st.subheader("Preview & Edit")

        ai["NATURE OF VIOLATION"] = st.text_input(
            "Nature of Violation",
            value=ai.get("NATURE OF VIOLATION", ""),
            key="w_edit_nat",
        )
        ai["ADDITIONAL COMMENTS"] = st.text_area(
            "Additional Comments (full narrative)",
            value=ai.get("ADDITIONAL COMMENTS", ""),
            height=300,
            key="w_edit_comments",
        )
        ai["REQUIRED IMPROVEMENTS"] = st.text_area(
            "Required Improvements (one per line)",
            value=ai.get("REQUIRED IMPROVEMENTS", ""),
            height=150,
            key="w_edit_improve",
        )
        ai["REVIEW PERIOD"] = st.text_input(
            "Review Period",
            value=ai.get("REVIEW PERIOD", "30-Day Review Period"),
            key="w_edit_period",
        )

        st.divider()
        if st.button("Download DOCX", key="w_download"):
            docx_bytes = build_warning_docx(
                employee_name=w_employee,
                job_title=w_title,
                department=w_department,
                date=w_date.strftime("%m/%d/%Y"),
                ai_content=ai,
            )
            filename = f"{w_date.strftime('%Y-%m-%d')}_{w_employee.replace(' ', '-')}_warning.docx"
            saved = _archive(docx_bytes, filename, "warnings")
            st.caption(f"Saved to `{saved}`")
            st.download_button(
                label="Download Warning Record",
                data=docx_bytes,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="w_dl_btn",
            )


# ---------------------------------------------------------------------------
# Tab 3: Annual Review
# ---------------------------------------------------------------------------

with tab_review:
    st.header("Annual Performance Review")

    # --- Clear button ---
    if st.button("Clear Form", key="r_clear"):
        for key in ["r_emp", "r_title", "r_dept", "r_pay", "r_pct",
                     "r_hire", "r_from", "r_to", "r_upload", "r_upload_bytes",
                     "r_last_upload_id", "r_parsed", "r_ai", "r_notes"]:
            st.session_state.pop(key, None)
        st.rerun()

    # --- Upload blank review ---
    uploaded_review = st.file_uploader(
        "Upload blank review (.docx only — if you have a .pages file, export it from Pages as Word first)",
        type=["docx"],
        key="r_upload",
    )

    # Parse uploaded file and push values into widget session state.
    # Track the upload ID to avoid re-parsing on rerun.
    if uploaded_review is not None:
        upload_id = uploaded_review.file_id
        if st.session_state.get("r_last_upload_id") != upload_id:
            file_bytes = uploaded_review.read()
            if file_bytes:
                st.session_state["r_upload_bytes"] = file_bytes
                st.session_state["r_last_upload_id"] = upload_id
                parsed = parse_review_docx(file_bytes)
                st.session_state["r_parsed"] = parsed

                # Push parsed values directly into widget keys
                st.session_state["r_emp"] = parsed.get("employee_name", "")
                st.session_state["r_title"] = parsed.get("job_title", "")
                st.session_state["r_dept"] = parsed.get("department", "")
                st.session_state["r_pay"] = parsed.get("current_pay", "")
                st.session_state["r_pct"] = parsed.get("percent_increase", "")

                hire_str = parsed.get("date_of_hire", "")
                if hire_str:
                    st.session_state["r_hire"] = _parse_date_str(hire_str)
                from_str = parsed.get("period_from", "")
                if from_str:
                    st.session_state["r_from"] = _parse_date_str(from_str)
                to_str = parsed.get("period_to", "")
                if to_str:
                    st.session_state["r_to"] = _parse_date_str(to_str)

                st.rerun()

        if "r_parsed" in st.session_state:
            name = st.session_state["r_parsed"].get("employee_name", "Unknown")
            st.success(f"Loaded review for **{name}**")

    col1, col2, col3 = st.columns(3)
    with col1:
        r_employee = st.text_input("Employee Name", key="r_emp")
        r_title = st.text_input("Job Title", key="r_title")
        r_department = st.text_input("Department", key="r_dept")
    with col2:
        r_hire = st.date_input("Date of Hire", key="r_hire")
        r_from = st.date_input("Review Period From", key="r_from")
        r_to = st.date_input("Review Period To", key="r_to")
    with col3:
        r_pay = st.text_input(
            "Current Pay Rate ($)", key="r_pay", placeholder="12.00",
        )
        r_pct = st.text_input(
            "Percent Increase (%)", key="r_pct", placeholder="3.0",
        )
        # Auto-calculate new pay rate
        r_new_pay = ""
        try:
            rate = float(r_pay)
            pct = float(r_pct)
            r_new_pay = f"${rate * (1 + pct / 100):.2f}"
        except (ValueError, TypeError):
            pass
        st.text_input("New Pay Rate", value=r_new_pay, disabled=True)

    r_notes = st.text_area(
        "Performance notes (AI will generate ratings, narrative, and 3 goals from this)",
        height=200,
        key="r_notes",
        placeholder="Describe the employee's performance: strengths, areas for improvement, notable accomplishments, attendance, attitude...",
    )

    if st.button("Generate Annual Review", type="primary", key="r_gen"):
        if not api_key:
            st.error("Enter your Anthropic API key in the sidebar.")
        elif not r_employee or not r_notes:
            st.error("Fill in employee name and performance notes.")
        else:
            with st.spinner("Generating annual review..."):
                client = get_client(api_key)
                ai = generate_annual_review(
                    client=client,
                    employee_name=r_employee,
                    job_title=r_title,
                    department=r_department,
                    date_of_hire=r_hire.strftime("%m/%d/%Y"),
                    period_from=r_from.strftime("%m/%d/%Y"),
                    period_to=r_to.strftime("%m/%d/%Y"),
                    current_pay=r_pay,
                    percent_increase=r_pct,
                    performance_notes=r_notes,
                )
                st.session_state["r_ai"] = ai

    if "r_ai" in st.session_state:
        ai = st.session_state["r_ai"]
        st.divider()
        st.subheader("Preview & Edit")

        # Trait ratings table
        st.markdown("**Performance Ratings**")
        traits = ai.get("trait_ratings_parsed", [])
        if traits:
            for i, t in enumerate(traits):
                cols = st.columns([3, 1, 4])
                with cols[0]:
                    st.text(t["trait"])
                with cols[1]:
                    t["rating"] = st.selectbox(
                        "Rating",
                        ["E", "AB", "G", "F", "U"],
                        index=["E", "AB", "G", "F", "U"].index(t["rating"]) if t["rating"] in ["E", "AB", "G", "F", "U"] else 2,
                        key=f"r_trait_{i}",
                        label_visibility="collapsed",
                    )
                with cols[2]:
                    t["comment"] = st.text_input(
                        "Comment",
                        value=t.get("comment", ""),
                        key=f"r_comment_{i}",
                        label_visibility="collapsed",
                    )

        ai["SUPERVISOR NARRATIVE"] = st.text_area(
            "Supervisor's Narrative",
            value=ai.get("SUPERVISOR NARRATIVE", ""),
            height=200,
            key="r_edit_narr",
        )
        ai["GOALS"] = st.text_area(
            "Goals for Current Year (3 goals, specific to position)",
            value=ai.get("GOALS", ""),
            height=150,
            key="r_edit_goals",
        )

        st.divider()
        if st.button("Download DOCX", key="r_download"):
            new_pay = ai.get("new_pay", "")
            template_bytes = st.session_state.get("r_upload_bytes")
            docx_bytes = build_annual_review_docx(
                ai_content=ai,
                supervisor_name=manager_name,
                template_bytes=template_bytes,
                employee_name=r_employee,
                job_title=r_title,
                department=r_department,
                date_of_hire=r_hire.strftime("%m/%d/%Y"),
                period_from=r_from.strftime("%m/%d/%Y"),
                period_to=r_to.strftime("%m/%d/%Y"),
                current_pay=r_pay,
                percent_increase=r_pct,
                new_pay=new_pay,
            )
            filename = f"{r_to.strftime('%Y-%m-%d')}_{r_employee.replace(' ', '-')}_annual-review.docx"
            saved = _archive(docx_bytes, filename, "reviews")
            st.caption(f"Saved to `{saved}`")
            st.download_button(
                label="Download Annual Review",
                data=docx_bytes,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="r_dl_btn",
            )


# ---------------------------------------------------------------------------
# Tab 4: Professional Development Plan
# ---------------------------------------------------------------------------

with tab_pdp:
    st.header("Professional Development Plan")

    # --- Upload existing PDP (scan, PDF, image, docx) ---
    uploaded_pdp = st.file_uploader(
        "Upload existing PDP to refine (PDF, image, or DOCX — scans and handwritten OK)",
        type=["pdf", "png", "jpg", "jpeg", "docx"],
        key="p_upload",
    )

    existing_pdp_context = ""
    if uploaded_pdp is not None:
        upload_id = uploaded_pdp.file_id
        if st.session_state.get("p_last_upload_id") != upload_id:
            file_bytes = uploaded_pdp.read()
            if file_bytes:
                st.session_state["p_upload_bytes"] = file_bytes
                st.session_state["p_upload_name"] = uploaded_pdp.name
                st.session_state["p_last_upload_id"] = upload_id
                st.success(f"Uploaded **{uploaded_pdp.name}** — AI will use this as reference")

        if "p_upload_bytes" in st.session_state:
            st.caption(f"Reference file: {st.session_state.get('p_upload_name', '')}")

    # --- Clear button ---
    if st.button("Clear Form", key="p_clear"):
        for key in ["p_emp", "p_pos", "p_loc", "p_goal", "p_notes",
                     "p_upload", "p_upload_bytes", "p_upload_name",
                     "p_last_upload_id", "p_ai"]:
            st.session_state.pop(key, None)
        st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        p_employee = st.text_input("Employee Name", key="p_emp")
        p_position = st.text_input("Position", key="p_pos")
    with col2:
        p_location = st.text_input("Work Location", key="p_loc")
        p_date = st.date_input("Date", value=datetime.now(), key="p_date")

    p_ultimate = st.text_input(
        "Employee's ultimate goal",
        key="p_goal",
        placeholder="e.g., Become a Store Manager within 2 years",
    )

    p_notes = st.text_area(
        "Development notes (what areas need growth? AI will generate goals and actions)",
        height=200,
        key="p_notes",
        placeholder="e.g., Needs to work on having difficult conversations with team. "
                    "Strong technically but avoids conflict. Good attendance, always on time. "
                    "Interested in moving into management...",
    )

    if st.button("Generate PDP", type="primary", key="p_gen"):
        if not api_key:
            st.error("Enter your Anthropic API key in the sidebar.")
        elif not p_employee or not p_notes:
            st.error("Fill in employee name and development notes.")
        else:
            # If there's an uploaded file, send it to Claude for context
            extra_context = ""
            if "p_upload_bytes" in st.session_state:
                upload_bytes = st.session_state["p_upload_bytes"]
                upload_name = st.session_state.get("p_upload_name", "")

                # Use Claude's vision for images/PDFs
                if upload_name.lower().endswith((".png", ".jpg", ".jpeg")):
                    import base64
                    b64 = base64.b64encode(upload_bytes).decode()
                    ext = upload_name.rsplit(".", 1)[-1].lower()
                    media = f"image/{ext}" if ext != "jpg" else "image/jpeg"
                    # We'll pass image context via a separate API call
                    client = get_client(api_key)
                    img_response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1500,
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}},
                                {"type": "text", "text": "Extract all text and data from this Professional Development Plan form. Include employee name, goals, types, whys, timeframes, and action steps. Return as structured text."},
                            ],
                        }],
                    )
                    extra_context = f"\n\nExisting PDP content to refine:\n{img_response.content[0].text}"

                elif upload_name.lower().endswith(".pdf"):
                    import base64
                    b64 = base64.b64encode(upload_bytes).decode()
                    client = get_client(api_key)
                    pdf_response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1500,
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64}},
                                {"type": "text", "text": "Extract all text and data from this Professional Development Plan form. Include employee name, goals, types, whys, timeframes, and action steps. Return as structured text."},
                            ],
                        }],
                    )
                    extra_context = f"\n\nExisting PDP content to refine:\n{pdf_response.content[0].text}"

                elif upload_name.lower().endswith(".docx"):
                    from docx import Document as DocxDoc
                    import io
                    ddoc = DocxDoc(io.BytesIO(upload_bytes))
                    text_parts = [p.text for p in ddoc.paragraphs if p.text.strip()]
                    for t in ddoc.tables:
                        for row in t.rows:
                            text_parts.append(" | ".join(c.text.strip() for c in row.cells))
                    extra_context = f"\n\nExisting PDP content to refine:\n" + "\n".join(text_parts)

            with st.spinner("Generating Professional Development Plan..."):
                client = get_client(api_key)
                notes_with_context = p_notes + extra_context
                ai = generate_pdp(
                    client=client,
                    employee_name=p_employee,
                    position=p_position,
                    location=p_location,
                    ultimate_goal=p_ultimate,
                    notes=notes_with_context,
                )
                st.session_state["p_ai"] = ai

    if "p_ai" in st.session_state:
        ai = st.session_state["p_ai"]
        st.divider()
        st.subheader("Preview & Edit")

        ai["ULTIMATE GOAL"] = st.text_input(
            "Ultimate Goal",
            value=ai.get("ULTIMATE GOAL", ""),
            key="p_edit_ultimate",
        )

        # Goals
        goals = ai.get("goals_parsed", [])
        for i, goal in enumerate(goals[:3]):
            st.markdown(f"**Goal {i+1}**")
            goal["goal"] = st.text_area(
                f"Goal {i+1}",
                value=goal.get("goal", ""),
                height=80,
                key=f"p_goal_{i}",
                label_visibility="collapsed",
            )
            cols = st.columns([2, 1])
            with cols[0]:
                goal["type"] = st.selectbox(
                    "Type",
                    ["Personal/Interpersonal Growth", "Technical/Job Skills",
                     "Leadership Capabilities", "Career Planning"],
                    index=["Personal/Interpersonal Growth", "Technical/Job Skills",
                           "Leadership Capabilities", "Career Planning"].index(goal["type"])
                    if goal["type"] in ["Personal/Interpersonal Growth", "Technical/Job Skills",
                                         "Leadership Capabilities", "Career Planning"] else 0,
                    key=f"p_type_{i}",
                )
            with cols[1]:
                goal["timeframe"] = st.selectbox(
                    "Timeframe",
                    ["1 month", "3 months", "6 months", "1 year"],
                    index=["1 month", "3 months", "6 months", "1 year"].index(goal["timeframe"])
                    if goal["timeframe"] in ["1 month", "3 months", "6 months", "1 year"] else 2,
                    key=f"p_tf_{i}",
                )
            goal["why"] = st.text_area(
                "My Why",
                value=goal.get("why", ""),
                height=80,
                key=f"p_why_{i}",
            )

        # Actions
        st.markdown("**Action Steps**")
        actions = ai.get("actions_parsed", [])
        for i, action in enumerate(actions[:6]):
            cols = st.columns([4, 1, 2])
            with cols[0]:
                action["action"] = st.text_input(
                    f"Action {i+1}",
                    value=action.get("action", ""),
                    key=f"p_action_{i}",
                )
            with cols[1]:
                action["goals"] = st.text_input(
                    "Goal(s)",
                    value=action.get("goals", ""),
                    key=f"p_agoal_{i}",
                )
            with cols[2]:
                action["support"] = st.text_input(
                    "Support",
                    value=action.get("support", ""),
                    key=f"p_asupport_{i}",
                )

        st.divider()
        if st.button("Download DOCX", key="p_download"):
            docx_bytes = build_pdp_docx(
                employee_name=p_employee,
                position=p_position,
                location=p_location,
                date=p_date.strftime("%m/%d/%Y"),
                ai_content=ai,
            )
            filename = f"{p_date.strftime('%Y-%m-%d')}_{p_employee.replace(' ', '-')}_pdp.docx"
            saved = _archive(docx_bytes, filename, "pdps")
            st.caption(f"Saved to `{saved}`")
            st.download_button(
                label="Download Development Plan",
                data=docx_bytes,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="p_dl_btn",
            )
