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

from ai_generator import get_client, generate_coaching, generate_warning, generate_annual_review, generate_pdp, parse_pdp_document
from doc_builder import build_coaching_docx, build_warning_docx, build_annual_review_docx, build_pdp_docx, build_pdp_pdf, build_pdp_fillable_pdf
from review_parser import parse_review_docx
from store_review import (
    STORE_ROSTER, load_all_metrics, save_report, reports_status,
    generate_store_review, build_store_review_xlsx,
)

# Load env
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env.local")

# Vault outputs directory — resolve to absolute path to avoid CWD issues
VAULT_OUTPUTS = Path(__file__).resolve().parent.parent.parent.parent / "outputs"


def _archive(docx_bytes: bytes, filename: str, doc_type: str):
    """Save generated doc to vault outputs folder. Skips silently if not writable (e.g. cloud)."""
    try:
        folder = VAULT_OUTPUTS / doc_type
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / filename
        path.write_bytes(docx_bytes)
        return path
    except Exception:
        return None

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
    "Lebanon",
    "Loveland",
    "Fairfield",
    "Beechmont",
    "Deerfield",
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

tab_coaching, tab_warning, tab_review, tab_pdp, tab_store_review = st.tabs([
    "Coaching Session",
    "Written Warning",
    "Annual Review",
    "Development Plan",
    "Store Review",
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
            if saved: st.caption(f"Saved to `{saved}`")
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
            if saved: st.caption(f"Saved to `{saved}`")
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
            if saved: st.caption(f"Saved to `{saved}`")
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
        file_bytes = uploaded_pdp.read()
        if file_bytes:
            st.session_state["p_upload_bytes"] = file_bytes
            st.session_state["p_upload_name"] = uploaded_pdp.name

        if "p_upload_bytes" in st.session_state:
            st.caption(f"Uploaded: {st.session_state.get('p_upload_name', '')}")
            if uploaded_pdp.name.lower().endswith(".pdf") and api_key:
                if st.button("Extract data from PDF", key="p_extract"):
                    parsed = parse_pdp_document(get_client(api_key), st.session_state["p_upload_bytes"])
                    st.session_state["p_emp"] = parsed.get("EMPLOYEE NAME", "")
                    st.session_state["p_pos"] = parsed.get("POSITION", "")
                    st.session_state["p_loc"] = parsed.get("LOCATION", "")
                    if parsed.get("DATE"):
                        st.session_state["p_date"] = _parse_date_str(parsed["DATE"]).date()
                    st.session_state["p_goal"] = parsed.get("ULTIMATE GOAL", "")
                    # Store as context for Generate PDP — don't set p_ai yet
                    ctx_lines = [
                        f"Ultimate Goal: {parsed.get('ULTIMATE GOAL', '')}",
                    ]
                    for i in range(1, 4):
                        if parsed.get(f"GOAL {i}"):
                            ctx_lines += [
                                f"Goal {i}: {parsed.get(f'GOAL {i}', '')}",
                                f"  Type: {parsed.get(f'GOAL {i} TYPE', '')}",
                                f"  Why: {parsed.get(f'GOAL {i} WHY', '')}",
                                f"  Timeframe: {parsed.get(f'GOAL {i} TIMEFRAME', '')}",
                            ]
                    for j, a in enumerate(parsed.get("actions_parsed", []), 1):
                        if a.get("action"):
                            ctx_lines.append(f"Action {j}: {a['action']} (Goal {a.get('goals','')}, Support: {a.get('support','')})")
                    st.session_state["p_pdf_context"] = "\n".join(ctx_lines)
                    st.rerun()

    # --- Clear button ---
    if st.button("Clear Form", key="p_clear"):
        for key in ["p_emp", "p_pos", "p_loc", "p_goal", "p_notes",
                     "p_upload", "p_upload_bytes", "p_upload_name",
                     "p_last_upload_id", "p_extract", "p_pdf_context", "p_ai"]:
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

    _has_pdf_context = "p_pdf_context" in st.session_state
    if _has_pdf_context:
        st.info("Existing PDP loaded — AI will use it as a base and suggest improvements. Add notes below to guide the refinement (optional).")

    p_notes = st.text_area(
        "Additional notes" if _has_pdf_context else "Development notes (AI will generate goals and actions from this)",
        height=150 if _has_pdf_context else 200,
        key="p_notes",
        placeholder="e.g., Focus on leadership development, preparing for GM role..." if _has_pdf_context
                    else "e.g., Needs to work on having difficult conversations with team. "
                         "Strong technically but avoids conflict. Good attendance, always on time. "
                         "Interested in moving into management...",
    )

    if st.button("Generate PDP", type="primary", key="p_gen"):
        if not api_key:
            st.error("Enter your Anthropic API key in the sidebar.")
        elif not p_employee:
            st.error("Fill in employee name.")
        elif not p_notes and not _has_pdf_context:
            st.error("Add development notes or upload and extract an existing PDP.")
        else:
            extra_context = ""
            if _has_pdf_context:
                extra_context = f"\n\nExisting PDP to use as a base — preserve and improve upon this content:\n{st.session_state['p_pdf_context']}"

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
        if st.button("Download PDF", key="p_download"):
            try:
                pdf_bytes = build_pdp_fillable_pdf(
                    employee_name=p_employee,
                    position=p_position,
                    location=p_location,
                    date=p_date.strftime("%m/%d/%Y"),
                    ai_content=ai,
                )
            except Exception as e:
                st.warning(f"Fillable PDF failed ({e}), using standard PDF.")
                pdf_bytes = build_pdp_pdf(
                    employee_name=p_employee,
                    position=p_position,
                    location=p_location,
                    date=p_date.strftime("%m/%d/%Y"),
                    ai_content=ai,
                )
            filename = f"{p_date.strftime('%Y-%m-%d')}_{p_employee.replace(' ', '-')}_pdp.pdf"
            saved = _archive(pdf_bytes, filename, "pdps")
            if saved: st.caption(f"Saved to `{saved}`")
            st.download_button(
                label="Download Development Plan (PDF)",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                key="p_dl_btn",
            )

# ---------------------------------------------------------------------------
# Tab 5: Store Review
# ---------------------------------------------------------------------------

with tab_store_review:
    st.header("Store Review Generator")

    # ── Report Status & Upload ────────────────────────────────────────────
    status = reports_status()
    with st.expander("📂 Data Reports on File", expanded=not all(status.values())):
        col_s, col_r, col_t = st.columns(3)
        with col_s:
            st.markdown("**Daily Sales Report**")
            if status["sales"]:
                st.success(f"On file — {status['sales']}")
            else:
                st.warning("Not uploaded yet")
            f = st.file_uploader("Upload latest sales report", type=["xlsx"], key="sr_sales_upload")
            if f and st.session_state.get("sr_sales_saved") != f.name:
                save_report(f.read(), "sales")
                st.session_state["sr_sales_saved"] = f.name
                st.success("Sales report saved.")
        with col_r:
            st.markdown("**Rack Units Report (Weekly)**")
            if status["rack"]:
                st.success(f"On file — {status['rack']}")
            else:
                st.warning("Not uploaded yet")
            f = st.file_uploader("Upload latest rack units report", type=["xlsx"], key="sr_rack_upload")
            if f and st.session_state.get("sr_rack_saved") != f.name:
                save_report(f.read(), "rack")
                st.session_state["sr_rack_saved"] = f.name
                st.success("Rack units report saved.")
        with col_t:
            st.markdown("**Turnover Report (Monthly)**")
            if status["turnover"]:
                st.success(f"On file — {status['turnover']}")
            else:
                st.warning("Not uploaded yet")
            f = st.file_uploader("Upload latest turnover report", type=["xlsx"], key="sr_turnover_upload")
            if f and st.session_state.get("sr_turnover_saved") != f.name:
                save_report(f.read(), "turnover")
                st.session_state["sr_turnover_saved"] = f.name
                st.success("Turnover report saved.")

    st.divider()

    # ── Store & Date Selection ─────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        sr_store = st.selectbox("Store", list(STORE_ROSTER.keys()), key="sr_store")
    with col2:
        sr_visit_date = st.date_input("Visit Date", value=datetime.now(), key="sr_visit_date")
    with col3:
        sr_prev_date = st.date_input("Previous Evaluation Date", value=datetime.now() - timedelta(days=21), key="sr_prev_date")

    # ── Clear AI cache if store changed since last generation ────────────────
    if st.session_state.get("sr_last_store") != sr_store:
        st.session_state.pop("sr_ai", None)
        st.session_state.pop("sr_metrics", None)
        st.session_state.pop("sr_manual", None)
    st.session_state["sr_last_store"] = sr_store

    # ── Clear Form button ─────────────────────────────────────────────────
    if st.button("Clear Form", key="sr_clear"):
        keys_to_clear = [k for k in st.session_state if k.startswith("sr_") and k not in ("sr_store", "sr_visit_date", "sr_prev_date", "sr_last_store")]
        for k in keys_to_clear:
            del st.session_state[k]
        st.rerun()

    # ── Auto-populated metrics ─────────────────────────────────────────────
    metrics = load_all_metrics(sr_store)

    roster = STORE_ROSTER[sr_store]
    sm_name = roster["sm"]
    asm_names = ", ".join(roster["asm"])

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"**Store Manager:** {sm_name}")
        st.markdown(f"**ASM(s):** {asm_names}")
    with col_b:
        if metrics:
            def fmt_pct(v): return f"{'+' if v and v >= 0 else ''}{(v or 0)*100:.1f}%" if v is not None else "—"
            st.markdown(f"**Rev % to Budget:** {fmt_pct(metrics.get('rev_pct_to_budget'))}")
            st.markdown(f"**Rev % to LY:** {fmt_pct(metrics.get('rev_pct_to_ly'))}")
            st.markdown(f"**Sell Through %:** {fmt_pct(metrics.get('sell_thru_pct'))}")
            u = metrics.get("units_over_under")
            st.markdown(f"**Unit Deficit:** {f'{u:,}' if u is not None else '—'}")
            t = metrics.get("ytd_turnover")
            st.markdown(f"**YTD Turnover:** {fmt_pct(t)}")
        else:
            st.info("Upload reports above to auto-populate metrics.")

    st.divider()

    # ── Manual Entry Fields ────────────────────────────────────────────────
    st.subheader("Visit Observations")

    col1, col2, col3 = st.columns(3)
    with col1:
        sr_labor       = st.number_input("Labor % to Budget", min_value=0.0, max_value=1.0, value=0.28, step=0.01, format="%.2f", key="sr_labor")
        sr_donation    = st.number_input("Donation Growth % to LY", min_value=-1.0, max_value=5.0, value=0.0, step=0.01, format="%.2f", key="sr_donation")
        sr_open_pos    = st.number_input("# Open Positions", min_value=0, max_value=20, value=0, key="sr_open_pos")
        sr_avg_trans   = st.number_input("Avg Transaction vs LY ($)", value=0.0, step=0.01, format="%.2f", key="sr_avg_trans")
    with col2:
        sr_ecomm_pct   = st.number_input("Ecommerce % to Budget", min_value=-1.0, max_value=5.0, value=0.0, step=0.01, format="%.2f", key="sr_ecomm_pct")
        sr_ecomm_totes = st.number_input("Ecommerce Totes MTD", min_value=0, value=0, key="sr_ecomm_totes")
        sr_truck       = st.selectbox("Truck Loaded Correctly?", ["Yes", "No"], key="sr_truck")
        sr_huddles     = st.selectbox("Huddles", ["Complete", "Incomplete"], key="sr_huddles")
        sr_huddle_days = st.number_input("# Days Missing (if incomplete)", min_value=0, value=0, key="sr_huddle_days")
    with col3:
        sr_rolling_racks = st.number_input("Rolling Racks Checked", min_value=0, value=0, key="sr_rolling_racks")
        sr_rack_items_back = st.number_input("Rolling Rack Items Sent Back", min_value=0, value=0, key="sr_rack_items_back")
        sr_hang_variance = st.number_input("Hang Count Variance", value=0.0, step=0.01, format="%.2f", key="sr_hang_variance")
        sr_tote_variance = st.number_input("Tote Count Variance", value=0.0, step=0.01, format="%.2f", key="sr_tote_variance")
        sr_totes_checked = st.number_input("Totes Checked", min_value=0, value=0, key="sr_totes_checked")
        sr_tote_items_back = st.number_input("Tote Items Sent Back", min_value=0, value=0, key="sr_tote_items_back")

    sr_employees_spoken = st.text_input("Hourly Employees Had 5-Min Conversation With (names)", key="sr_employees_spoken")
    sr_new_hires_met    = st.number_input("New Hires Met", min_value=0, value=0, key="sr_new_hires_met")
    sr_num_new_hires    = st.number_input("Number of New Hires", min_value=0, value=0, key="sr_num_new_hires")

    # Yes/No observation fields
    st.markdown("**Merchandising**")
    mc1, mc2, mc3, mc4 = st.columns(4)
    sr_merch_wares   = mc1.selectbox("Wares Shelves Full", ["Yes", "No"], key="sr_m_wares")
    sr_merch_racks   = mc2.selectbox("Racks Full", ["Yes", "No"], key="sr_m_racks")
    sr_merch_shoes   = mc3.selectbox("Shoe Racks Full", ["Yes", "No"], key="sr_m_shoes")
    sr_merch_endcaps = mc4.selectbox("End Caps Full", ["Yes", "No"], key="sr_m_endcaps")

    st.markdown("**Store Cleanliness**")
    cc1, cc2, cc3 = st.columns(3)
    sr_clean_parking  = cc1.selectbox("Parking Lot",    ["Yes", "No"], key="sr_c_parking")
    sr_clean_donation = cc1.selectbox("Donation Area",  ["Yes", "No"], key="sr_c_donation")
    sr_clean_windows  = cc1.selectbox("Windows/Entry",  ["Yes", "No"], key="sr_c_windows")
    sr_clean_cashwrap = cc2.selectbox("Cash Wraps",     ["Yes", "No"], key="sr_c_cashwrap")
    sr_clean_floor    = cc2.selectbox("Floor/Racks",    ["Yes", "No"], key="sr_c_floor")
    sr_clean_wares    = cc2.selectbox("Wares/Shelves",  ["Yes", "No"], key="sr_c_wares")
    sr_clean_fitting  = cc3.selectbox("Fitting Rooms",  ["Yes", "No"], key="sr_c_fitting")
    sr_clean_prod     = cc3.selectbox("Production Room",["Yes", "No"], key="sr_c_prod")
    sr_clean_offices  = cc3.selectbox("Offices",        ["Yes", "No"], key="sr_c_offices")

    st.markdown("**Pull/Rotation Validation**")
    pc1, pc2, pc3, pc4 = st.columns(4)
    sr_pull_womens = pc1.selectbox("Women's Rack", ["Yes", "No"], key="sr_p_womens")
    sr_pull_mens   = pc1.selectbox("Men's Rack",   ["Yes", "No"], key="sr_p_mens")
    sr_pull_kids   = pc2.selectbox("Kid's Rack",   ["Yes", "No"], key="sr_p_kids")
    sr_pull_wares  = pc2.selectbox("Wares",        ["Yes", "No"], key="sr_p_wares")
    sr_pull_shoes  = pc3.selectbox("Shoes",        ["Yes", "No"], key="sr_p_shoes")
    sr_pull_books  = pc3.selectbox("Books",        ["Yes", "No"], key="sr_p_books")
    sr_pull_em     = pc4.selectbox("E&M",          ["Yes", "No"], key="sr_p_em")

    st.markdown("**Error Rate — Racks**")
    er1, er2, er3, er4 = st.columns(4)
    sr_err_total    = er1.number_input("Total Items Checked", min_value=0, value=0, key="sr_err_total")
    sr_err_price    = er2.number_input("# Wrong Price",        min_value=0, value=0, key="sr_err_price")
    sr_err_defect   = er3.number_input("# Defective",          min_value=0, value=0, key="sr_err_defect")
    sr_err_category = er4.number_input("# Wrong Category/Size",min_value=0, value=0, key="sr_err_category")

    st.markdown("**Error Rate — Container Labels**")
    cl1, cl2, cl3 = st.columns(3)
    sr_con_total       = cl1.number_input("Total Containers Checked",      min_value=0, value=0, key="sr_con_total")
    sr_con_unlabeled   = cl1.number_input("Not Labeled",                   min_value=0, value=0, key="sr_con_unlabeled")
    sr_con_salv_raw    = cl2.number_input("Labeled Salvage but is Raw",    min_value=0, value=0, key="sr_con_salv_raw")
    sr_con_raw_salv    = cl2.number_input("Labeled Raw but is Salvage",    min_value=0, value=0, key="sr_con_raw_salv")
    sr_con_soft_hard   = cl3.number_input("Labeled Soft but is Hard",      min_value=0, value=0, key="sr_con_soft_hard")
    sr_con_hard_soft   = cl3.number_input("Labeled Hard but is Soft",      min_value=0, value=0, key="sr_con_hard_soft")

    sr_carry_overs = st.text_area(
        "Carry-over priorities from last visit (briefly describe what's still incomplete)",
        height=80, key="sr_carry_overs",
        placeholder="e.g., Unit deficit still -4,500 (was priority 1 last visit). Spring flip still incomplete."
    )
    sr_notes = st.text_area(
        "Additional visit notes (anything else to factor in)",
        height=80, key="sr_notes",
        placeholder="e.g., HR involved with one team member. Donation counts were off. Store ran out of price tags."
    )

    st.divider()

    # ── Generate ──────────────────────────────────────────────────────────
    if st.button("Generate Store Review", type="primary", key="sr_generate"):
        if not api_key:
            st.error("API key required.")
        else:
            manual = {
                "visit_date":              sr_visit_date.strftime("%m/%d/%Y"),
                "labor_pct_to_budget":     sr_labor,
                "donation_growth_pct_ly":  sr_donation,
                "open_positions":          sr_open_pos,
                "avg_transaction_vs_ly":   sr_avg_trans,
                "ecommerce_pct_to_budget": sr_ecomm_pct,
                "ecommerce_totes_mtd":     sr_ecomm_totes,
                "truck_loaded":            sr_truck,
                "huddles":                 sr_huddles,
                "huddles_days_missing":    sr_huddle_days if sr_huddles == "Incomplete" else 0,
                "rolling_racks_checked":   sr_rolling_racks,
                "rolling_rack_items_back": sr_rack_items_back,
                "hang_count_variance":     sr_hang_variance,
                "tote_count_variance":     sr_tote_variance,
                "totes_checked":           sr_totes_checked,
                "tote_items_back":         sr_tote_items_back,
                "employees_spoken_to":     sr_employees_spoken,
                "new_hires_met":           sr_new_hires_met,
                "num_new_hires":           sr_num_new_hires,
                "merch_wares_full":        sr_merch_wares,
                "merch_racks_full":        sr_merch_racks,
                "merch_shoe_racks_full":   sr_merch_shoes,
                "merch_end_caps_full":     sr_merch_endcaps,
                "clean_parking_lot":       sr_clean_parking,
                "clean_donation_area":     sr_clean_donation,
                "clean_windows_entry":     sr_clean_windows,
                "clean_cash_wraps":        sr_clean_cashwrap,
                "clean_floor_racks":       sr_clean_floor,
                "clean_wares_shelves":     sr_clean_wares,
                "clean_fitting_rooms":     sr_clean_fitting,
                "clean_production_room":   sr_clean_prod,
                "clean_offices":           sr_clean_offices,
                "pull_womens":             sr_pull_womens,
                "pull_mens":               sr_pull_mens,
                "pull_kids":               sr_pull_kids,
                "pull_wares":              sr_pull_wares,
                "pull_shoes":              sr_pull_shoes,
                "pull_books":              sr_pull_books,
                "pull_em":                 sr_pull_em,
                "error_total_items":       sr_err_total,
                "error_wrong_price":       sr_err_price,
                "error_defective":         sr_err_defect,
                "error_wrong_category":    sr_err_category,
                "container_total":         sr_con_total,
                "container_not_labeled":   sr_con_unlabeled,
                "container_salvage_as_raw":sr_con_salv_raw,
                "container_raw_as_salvage":sr_con_raw_salv,
                "container_soft_as_hard":  sr_con_soft_hard,
                "container_hard_as_soft":  sr_con_hard_soft,
                "carry_over_priorities":   sr_carry_overs,
                "additional_notes":        sr_notes,
            }
            with st.spinner("Generating store review content..."):
                try:
                    ai = generate_store_review(get_client(api_key), sr_store, metrics, manual)
                    st.session_state["sr_ai"] = ai
                    st.session_state["sr_manual"] = manual
                    st.session_state["sr_metrics"] = metrics
                except Exception as e:
                    st.error(f"Generation failed: {e}")

    # ── Preview & Edit ────────────────────────────────────────────────────
    if "sr_ai" in st.session_state:
        ai = st.session_state["sr_ai"]
        st.subheader("Generated Content — Review & Edit")

        ai["comments"] = st.text_area(
            "General Store Comments",
            value=ai.get("comments", ""),
            height=250,
            key="sr_comments_edit",
        )

        for i, p in enumerate(ai.get("priorities", [])[:3]):
            st.markdown(f"**Priority {i+1}**")
            c1, c2 = st.columns(2)
            p["opportunity"] = c1.text_area(
                "Opportunity", value=p.get("opportunity", ""), height=100, key=f"sr_opp_{i}"
            )
            p["action_plan"] = c2.text_area(
                "Action Plan / SMART Goal", value=p.get("action_plan", ""), height=100, key=f"sr_plan_{i}"
            )

        st.divider()
        if st.button("Download Store Review", type="primary", key="sr_download"):
            xlsx = build_store_review_xlsx(
                store=sr_store,
                visit_date=sr_visit_date.strftime("%m/%d/%Y"),
                prev_date=sr_prev_date.strftime("%m/%d/%Y"),
                metrics=st.session_state["sr_metrics"],
                manual=st.session_state["sr_manual"],
                ai_content=ai,
            )
            filename = f"{sr_visit_date.strftime('%Y-%m-%d')}_{sr_store.replace(' ', '-')}_store-review.xlsx"
            saved = _archive(xlsx, filename, "store-reviews")
            if saved: st.caption(f"Saved to `{saved}`")
            st.download_button(
                label="Download Store Review (Excel)",
                data=xlsx,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="sr_dl_btn",
            )
