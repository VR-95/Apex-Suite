# ─────────────────────────────────────────────────────────────────────────────
#  APEX SUITE  ·  FINAL MVP  (Session 4 — 11 Modules)
#  Modules: Resume Builder · Portfolio Builder · Career Intelligence
#           Cover Letter · LinkedIn Generator · Cold Outreach · Salary Estimator
#           Mock Interviewer · Application Tracker
#           Skill-Gap Roadmap · Interview Cheat Sheet
#  Stack:   Streamlit · Groq (Llama 3.3 70B) · fpdf2 · python-pptx · Plotly · SQLite
# ─────────────────────────────────────────────────────────────────────────────

import io
import json
import os
import sqlite3
import datetime

import streamlit as st
from dotenv import load_dotenv
from fpdf import FPDF
from groq import Groq
from pptx import Presentation

try:
    import plotly.graph_objects as go
    PLOTLY = True
except ImportError:
    PLOTLY = False

# ── SETUP ─────────────────────────────────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")

st.set_page_config(
    page_title="Apex Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not API_KEY:
    st.error("⚠️ **GROQ_API_KEY** missing — add it to your `.env` file and restart.")
    st.code("GROQ_API_KEY=gsk_your_key_here", language="bash")
    st.stop()

client = Groq(api_key=API_KEY)
MODEL  = "llama-3.3-70b-versatile"

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Hero banner */
.hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
    padding: 3rem 2rem;
    border-radius: 16px;
    text-align: center;
    margin-bottom: 2rem;
}
.hero h1 {
    color: white;
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: -1px;
    margin-bottom: 0.4rem;
}
.hero p { color: #94a3b8; font-size: 1.05rem; margin: 0; }

/* Module card */
.card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem 1.25rem;
    text-align: center;
}
.card .icon  { font-size: 2.4rem; margin-bottom: 0.6rem; }
.card h3     { font-size: 1.1rem; font-weight: 700; margin-bottom: 0.35rem; }
.card p      { color: #64748b; font-size: 0.85rem; margin: 0; }

/* Skill chips */
.chip {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 99px;
    font-size: 0.76rem;
    font-weight: 600;
    margin: 2px 2px;
}
.chip-g { background: #dcfce7; color: #15803d; }   /* matched required  */
.chip-r { background: #fee2e2; color: #b91c1c; }   /* missing required  */
.chip-b { background: #dbeafe; color: #1d4ed8; }   /* matched preferred */
.chip-y { background: #fef9c3; color: #a16207; }   /* missing preferred */
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ──────────────────────────────────────────────────────────────
_D = {
    "page": "hub", "step": 1,
    # Resume Builder
    "r_name": "", "r_email": "", "r_phone": "",
    "r_linkedin": "", "r_github": "",
    "r_edu": "", "r_skills": "", "r_exp": "", "r_proj": "",
    "r_ai_edu": "", "r_ai_skills": "", "r_ai_exp": [], "r_ai_proj": [],
    "r_blob": "",          # plain-text resume blob → feeds Career Intelligence
    # Portfolio Builder
    "p_name": "", "p_tagline": "", "p_about": "", "p_projects": "",
    "p_slides": [],
    # Career Intelligence
    "ci_role": "", "ci_jd": "", "ci_resume_paste": "", "ci_result": None,
    # Cover Letter Generator
    "cl_role": "", "cl_company": "", "cl_jd": "", "cl_your_name": "", "cl_output": "",
    # LinkedIn Generator
    "li_output_about": "", "li_output_headline": "", "li_output_summary": "",
    # Cold Outreach Generator
    "co_role": "", "co_company": "", "co_manager": "", "co_context": "", "co_output": "",
    # Salary Estimator
    "sal_role": "", "sal_exp": "0", "sal_skills": "",
    "sal_location": "", "sal_result": None,
    # Mock Interviewer
    "mi_role": "", "mi_jd": "",
    "mi_questions": [], "mi_current_q": 0,
    "mi_answers": [], "mi_scores": [],
    "mi_interview_done": False, "mi_report": None,
    "mi_setup_done": False,
    # Skill-Gap Roadmap
    "sg_role": "", "sg_skills": "", "sg_weeks": "4", "sg_result": None,
    # Interview Cheat Sheet
    "cs_role": "", "cs_company": "", "cs_jd": "", "cs_result": None,
}
for k, v in _D.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── GROQ HELPERS ───────────────────────────────────────────────────────────────
def gj(system: str, user: str):
    """Groq call → JSON dict. Returns (data, error_str)."""
    try:
        r = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            model=MODEL,
            response_format={"type": "json_object"},
        )
        return json.loads(r.choices[0].message.content), None
    except Exception as e:
        return None, str(e)

def gt(system: str, user: str):
    """Groq call → plain text. Returns (text, error_str)."""
    try:
        r = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            model=MODEL,
        )
        return r.choices[0].message.content, None
    except Exception as e:
        return None, str(e)

# ── SMALL UTILITIES ────────────────────────────────────────────────────────────
def strip_tags(t: str) -> str:
    return str(t).replace("<b>","").replace("</b>","").replace("<i>","").replace("</i>","")

def latin(t: str) -> str:
    return strip_tags(t).encode("latin-1", "replace").decode("latin-1")

def chips(skills: list, cls: str) -> str:
    return " ".join(f'<span class="chip {cls}">{s}</span>' for s in skills)

# ── APPLICATION TRACKER — SQLite helpers ───────────────────────────────────────
AT_DB = "apex_tracker.db"
AT_STATUSES = [
    "Applied", "Phone Screen", "Technical Interview",
    "Final Round", "Offer 🎉", "Rejected",
]
AT_COLORS = {
    "Applied":              "#3b82f6",
    "Phone Screen":         "#f59e0b",
    "Technical Interview":  "#8b5cf6",
    "Final Round":          "#ec4899",
    "Offer 🎉":             "#10b981",
    "Rejected":             "#ef4444",
}

def at_init():
    con = sqlite3.connect(AT_DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            company      TEXT NOT NULL,
            role         TEXT NOT NULL,
            status       TEXT DEFAULT 'Applied',
            date_applied TEXT,
            jd_url       TEXT,
            notes        TEXT,
            salary_range TEXT,
            contact      TEXT,
            next_action  TEXT,
            created_at   TEXT
        )
    """)
    con.commit(); con.close()

def at_add(company, role, status, date_applied,
           jd_url, notes, salary_range, contact, next_action):
    con = sqlite3.connect(AT_DB)
    con.execute(
        "INSERT INTO applications (company,role,status,date_applied,jd_url,"
        "notes,salary_range,contact,next_action,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (company, role, status, date_applied, jd_url, notes,
         salary_range, contact, next_action,
         datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    con.commit(); con.close()

def at_all():
    con = sqlite3.connect(AT_DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT * FROM applications ORDER BY created_at DESC"
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]

def at_set_status(app_id, status):
    con = sqlite3.connect(AT_DB)
    con.execute("UPDATE applications SET status=? WHERE id=?", (status, app_id))
    con.commit(); con.close()

def at_save_notes(app_id, notes, next_action):
    con = sqlite3.connect(AT_DB)
    con.execute(
        "UPDATE applications SET notes=?,next_action=? WHERE id=?",
        (notes, next_action, app_id),
    )
    con.commit(); con.close()

def at_delete(app_id):
    con = sqlite3.connect(AT_DB)
    con.execute("DELETE FROM applications WHERE id=?", (app_id,))
    con.commit(); con.close()

at_init()   # create table on every startup (idempotent)

# ── SIDEBAR NAVIGATION ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚡ Apex Suite")
    st.caption("AI Career Intelligence Platform")
    st.divider()
    for label, key in [
        ("🏠  Hub",                "hub"),
        ("📄  Resume Builder",     "resume"),
        ("🖼️  Portfolio Builder",  "portfolio"),
        ("🎯  Career Intelligence","career"),
        ("✉️  Cover Letter",       "coverletter"),
        ("🔗  LinkedIn Generator", "linkedin"),
        ("📨  Cold Outreach",      "coldoutreach"),
        ("💰  Salary Estimator",   "salary"),
        ("🎤  Mock Interviewer",   "interview"),
        ("📋  App Tracker",        "tracker"),
        ("📚  Skill-Gap Roadmap",  "roadmap"),
        ("📝  Cheat Sheet",        "cheatsheet"),
    ]:
        active = st.session_state.page == key
        if st.button(label, key=f"nav_{key}", use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state.page = key
            st.session_state.step = 1
            st.rerun()
    st.divider()
    st.caption("Model · Groq Llama 3.3 70B")

# ══════════════════════════════════════════════════════════════════════════════
#  HUB
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.page == "hub":
    st.markdown("""
    <div class="hero">
      <h1>⚡ Apex Suite</h1>
      <p>Build your resume, create your portfolio, and land the right job — all in one AI-powered platform.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3, gap="large")
    modules = [
        ("📄", "Resume Builder",
         "Turn rough notes into a polished, ATS-ready PDF with AI bullet points.", "resume"),
        ("🖼️", "Portfolio Builder",
         "Generate a 7-slide PowerPoint deck from your notes in seconds.", "portfolio"),
        ("🎯", "Career Intelligence",
         "Get your ATS match score, skill-gap chart, and AI suggestions for any JD.", "career"),
    ]
    for col, (icon, title, desc, key) in zip([c1, c2, c3], modules):
        with col:
            st.markdown(
                f'<div class="card"><div class="icon">{icon}</div>'
                f'<h3>{title}</h3><p>{desc}</p></div>',
                unsafe_allow_html=True,
            )
            st.markdown("")
            if st.button(f"Open {title} →", key=f"hub_{key}",
                         use_container_width=True, type="primary"):
                st.session_state.page = key
                st.session_state.step = 1
                st.rerun()

    # ── Row 2: New modules ────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    r2c1, r2c2, r2c3, r2c4, r2c5 = st.columns(5, gap="medium")
    new_modules = [
        ("✉️", "Cover Letter",      "AI-tailored cover letters from resume + JD.",  "coverletter"),
        ("🔗", "LinkedIn Generator","AI headline, About section & brand tagline.",   "linkedin"),
        ("📨", "Cold Outreach",     "DMs and cold emails that actually get replies.","coldoutreach"),
        ("💰", "Salary Estimator",  "Salary range by role, skills & location.",      "salary"),
        ("📋", "App Tracker",       "Kanban board — track every job application.",   "tracker"),
    ]
    for col, (icon, title, desc, key) in zip(
        [r2c1, r2c2, r2c3, r2c4, r2c5], new_modules
    ):
        with col:
            st.markdown(
                f'<div class="card"><div class="icon">{icon}</div>'
                f'<h3>{title}</h3><p>{desc}</p></div>',
                unsafe_allow_html=True,
            )
            st.markdown("")
            if st.button(f"Open →", key=f"hub2_{key}",
                         use_container_width=True, type="primary"):
                st.session_state.page = key
                st.session_state.step = 1
                st.rerun()

    # ── Row 3: Flagship module ────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🌟 Flagship Feature")
    _, feat_col, _ = st.columns([1, 3, 1])
    with feat_col:
        st.markdown("""
        <div class="card" style="background:linear-gradient(135deg,#1e3a5f,#0f172a);
             color:white;border:none;padding:2rem;">
          <div class="icon">🎤</div>
          <h3 style="color:white;">AI Mock Interviewer</h3>
          <p style="color:#94a3b8;">Role-specific questions · Per-answer AI scoring ·
          Full PDF report with strengths, gaps &amp; a 7-day study plan.</p>
        </div>""", unsafe_allow_html=True)
        st.markdown("")
        if st.button("🎤 Launch Mock Interviewer →", key="hub3_interview",
                     use_container_width=True, type="primary"):
            st.session_state.page = "interview"
            st.session_state.step = 1
            st.rerun()

    # ── Row 4: Prep modules ───────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    r4c1, r4c2 = st.columns(2, gap="large")
    prep_modules = [
        ("📚", "Skill-Gap Roadmap",
         "Week-by-week learning plan for your missing skills with free resources.",
         "roadmap"),
        ("📝", "Interview Cheat Sheet",
         "1-page AI prep brief for any company + role + round — ready in 30 seconds.",
         "cheatsheet"),
    ]
    for col, (icon, title, desc, key) in zip([r4c1, r4c2], prep_modules):
        with col:
            st.markdown(
                f'<div class="card"><div class="icon">{icon}</div>'
                f'<h3>{title}</h3><p>{desc}</p></div>',
                unsafe_allow_html=True,
            )
            st.markdown("")
            if st.button(f"Open {title} →", key=f"hub4_{key}",
                         use_container_width=True, type="primary"):
                st.session_state.page = key
                st.session_state.step = 1
                st.rerun()

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("AI Model",    "Llama 3.3 · 70B")
    m2.metric("Modules",     "11 Active")
    m3.metric("Export",      "PDF · PPTX")
    m4.metric("ATS Analysis","Real-time")

# ══════════════════════════════════════════════════════════════════════════════
#  RESUME BUILDER
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "resume":
    TOTAL = 6
    step  = st.session_state.step
    st.title("📄 Resume Builder")
    st.progress(step / TOTAL, text=f"Step {step} of {TOTAL}")
    st.divider()

    # ── Step 1: Contact ────────────────────────────────────────────────────────
    if step == 1:
        st.subheader("Step 1 — Contact Information")
        a, b = st.columns(2)
        st.session_state.r_name  = a.text_input("Full Name *",    st.session_state.r_name)
        st.session_state.r_email = b.text_input("Email *",         st.session_state.r_email)
        st.session_state.r_phone = a.text_input("Phone Number *",  st.session_state.r_phone)
        if st.button("Next →", type="primary"):
            if st.session_state.r_name and st.session_state.r_email:
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("Name and email are required.")

    # ── Step 2: Links ──────────────────────────────────────────────────────────
    elif step == 2:
        st.subheader("Step 2 — Professional Links")
        st.session_state.r_linkedin = st.text_input(
            "LinkedIn URL", st.session_state.r_linkedin,
            placeholder="https://linkedin.com/in/yourname")
        st.session_state.r_github = st.text_input(
            "GitHub URL", st.session_state.r_github,
            placeholder="https://github.com/yourusername")
        a, b = st.columns(2)
        if a.button("← Back"):                  st.session_state.step = 1; st.rerun()
        if b.button("Next →", type="primary"):  st.session_state.step = 3; st.rerun()

    # ── Step 3: Education & Skills ─────────────────────────────────────────────
    elif step == 3:
        st.subheader("Step 3 — Education & Skills")
        st.caption("Write rough notes — AI will polish these into professional language.")
        st.session_state.r_edu = st.text_area(
            "Education", st.session_state.r_edu, height=110,
            placeholder="e.g. B.Tech CSE, XYZ University, 2022–2026, CGPA 8.5")
        st.session_state.r_skills = st.text_area(
            "Skills & Technologies", st.session_state.r_skills, height=110,
            placeholder="e.g. Python, Machine Learning, SQL, React, Docker, Power BI")
        a, b = st.columns(2)
        if a.button("← Back"):                  st.session_state.step = 2; st.rerun()
        if b.button("Next →", type="primary"):  st.session_state.step = 4; st.rerun()

    # ── Step 4: Experience ─────────────────────────────────────────────────────
    elif step == 4:
        st.subheader("Step 4 — Work Experience")
        st.caption("Rough notes → 4 powerful AI-polished bullets.")
        st.session_state.r_exp = st.text_area(
            "Experience", st.session_state.r_exp, height=170,
            placeholder="e.g. Data Science Intern at ABC Corp, built churn model, "
                        "reduced attrition by 22%, used Python/XGBoost...")
        a, b = st.columns(2)
        if a.button("← Back"):                  st.session_state.step = 3; st.rerun()
        if b.button("Next →", type="primary"):  st.session_state.step = 5; st.rerun()

    # ── Step 5: Projects → AI Generate ─────────────────────────────────────────
    elif step == 5:
        st.subheader("Step 5 — Projects")
        st.caption("Rough notes → 4 impactful AI-polished bullets.")
        st.session_state.r_proj = st.text_area(
            "Projects", st.session_state.r_proj, height=170,
            placeholder="e.g. Built NLP-based fake-news detector, 94% accuracy, "
                        "deployed on Streamlit, used HuggingFace transformers...")
        a, b = st.columns(2)
        if a.button("← Back"): st.session_state.step = 4; st.rerun()
        if b.button("⚡ Generate with AI", type="primary"):
            with st.spinner("Llama 3.3 is writing your resume content..."):
                data, err = gj(
                    system=(
                        "Expert executive resume writer. Output JSON only.\n"
                        'Schema: {"edu":"str","skills":"str","exp":["","","",""],"proj":["","","",""]}\n'
                        "Wrap metrics/key results in <b> tags. Wrap tool/tech names in <i> tags.\n"
                        "exp and proj must contain exactly 4 detailed, achievement-focused bullets each."
                    ),
                    user=(
                        f"Education: {st.session_state.r_edu}\n"
                        f"Skills: {st.session_state.r_skills}\n"
                        f"Experience: {st.session_state.r_exp}\n"
                        f"Projects: {st.session_state.r_proj}"
                    ),
                )
            if err:
                st.error(f"Groq error: {err}")
            else:
                st.session_state.r_ai_edu    = data.get("edu",    "")
                st.session_state.r_ai_skills = data.get("skills", "")
                st.session_state.r_ai_exp    = data.get("exp",    [])
                st.session_state.r_ai_proj   = data.get("proj",   [])
                st.session_state.step = 6
                st.rerun()

    # ── Step 6: Review & Download ──────────────────────────────────────────────
    elif step == 6:
        st.subheader("Step 6 — Review & Download")

        with st.expander("📚 Education & Skills", expanded=True):
            st.markdown(f"**Education:** {st.session_state.r_ai_edu}",    unsafe_allow_html=True)
            st.markdown(f"**Skills:** {st.session_state.r_ai_skills}", unsafe_allow_html=True)

        with st.expander("💼 Experience — tick bullets to include", expanded=True):
            sel_exp = [
                b for i, b in enumerate(st.session_state.r_ai_exp)
                if st.checkbox(b, value=True, key=f"re{i}")
            ]

        with st.expander("🚀 Projects — tick bullets to include", expanded=True):
            sel_proj = [
                b for i, b in enumerate(st.session_state.r_ai_proj)
                if st.checkbox(b, value=True, key=f"rp{i}")
            ]

        st.divider()
        a, b = st.columns(2)
        if a.button("← Back to Notes"):
            st.session_state.step = 5
            st.rerun()

        if b.button("📥 Download PDF Resume", type="primary"):
            # Persist plain-text blob for Career Intelligence ATS checker
            st.session_state.r_blob = " ".join([
                st.session_state.r_name,
                st.session_state.r_ai_edu,
                st.session_state.r_ai_skills,
                *sel_exp,
                *sel_proj,
            ])

            # Build PDF entirely in memory — no shared disk files
            pdf = FPDF()
            pdf.add_page()

            def sec(title: str) -> None:
                pdf.set_font("Helvetica", "B", 13)
                pdf.cell(0, 8, latin(title), ln=True)
                pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                pdf.ln(3)

            # Header
            pdf.set_font("Helvetica", "B", 22)
            pdf.cell(0, 12, latin(st.session_state.r_name.upper()), align="C", ln=True)
            pdf.set_font("Helvetica", "", 10)
            contact = f"{st.session_state.r_email} | {st.session_state.r_phone}"
            if st.session_state.r_linkedin:
                contact += f" | {st.session_state.r_linkedin}"
            if st.session_state.r_github:
                contact += f" | {st.session_state.r_github}"
            pdf.cell(0, 5, latin(contact), align="C", ln=True)
            pdf.ln(6)

            if st.session_state.r_ai_edu:
                sec("EDUCATION")
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(0, 5, latin(st.session_state.r_ai_edu))
                pdf.ln(3)

            if sel_exp:
                sec("EXPERIENCE")
                pdf.set_font("Helvetica", "", 10)
                for bullet in sel_exp:
                    pdf.multi_cell(0, 5, latin(f"•  {bullet}"))
                    pdf.ln(1)
                pdf.ln(2)

            if sel_proj:
                sec("PROJECTS")
                pdf.set_font("Helvetica", "", 10)
                for bullet in sel_proj:
                    pdf.multi_cell(0, 5, latin(f"•  {bullet}"))
                    pdf.ln(1)
                pdf.ln(2)

            if st.session_state.r_ai_skills:
                sec("SKILLS")
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(0, 5, latin(st.session_state.r_ai_skills))

            fname = (st.session_state.r_name or "Apex").replace(" ", "_")
            st.download_button(
                label="⬇️  Save Resume PDF",
                data=pdf.output(),          # bytes — no disk write
                file_name=f"{fname}_Resume.pdf",
                mime="application/pdf",
            )
            st.success("✅ Resume ready! It's also auto-saved for the ATS Checker in Career Intelligence.")

# ══════════════════════════════════════════════════════════════════════════════
#  PORTFOLIO BUILDER
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "portfolio":
    TOTAL = 3
    step  = st.session_state.step
    st.title("🖼️ Portfolio Builder")
    st.progress(step / TOTAL, text=f"Step {step} of {TOTAL}")
    st.divider()

    # ── Step 1 ─────────────────────────────────────────────────────────────────
    if step == 1:
        st.subheader("Step 1 — Your Identity")
        st.session_state.p_name    = st.text_input("Full Name", st.session_state.p_name)
        st.session_state.p_tagline = st.text_input(
            "Professional Tagline", st.session_state.p_tagline,
            placeholder="Data Scientist | ML Engineer | Open Source Contributor")
        if st.button("Next →", type="primary"):
            if st.session_state.p_name:
                st.session_state.step = 2
                st.rerun()
            else:
                st.error("Name is required.")

    # ── Step 2 ─────────────────────────────────────────────────────────────────
    elif step == 2:
        st.subheader("Step 2 — Your Story & Work")
        st.session_state.p_about = st.text_area(
            "About Me", st.session_state.p_about, height=130,
            placeholder="What drives you? Your background, what you love building...")
        st.session_state.p_projects = st.text_area(
            "Projects & Achievements", st.session_state.p_projects, height=200,
            placeholder="Describe 2–3 of your best projects with outcomes, tools, and impact...")
        a, b = st.columns(2)
        if a.button("← Back"): st.session_state.step = 1; st.rerun()
        if b.button("⚡ Generate Slides", type="primary"):
            with st.spinner("Groq is building your deck..."):
                data, err = gj(
                    system='JSON-only API. Schema: {"slides":[{"title":"str","content":"str"}]}',
                    user=(
                        f"Name: {st.session_state.p_name}\n"
                        f"Tagline: {st.session_state.p_tagline}\n"
                        f"About: {st.session_state.p_about}\n"
                        f"Projects: {st.session_state.p_projects}\n\n"
                        "Create exactly 6 slides in order: "
                        "1) About Me  2) Technical Skills  3) Project Showcase 1  "
                        "4) Project Showcase 2  5) Achievements & Impact  6) Let's Connect"
                    ),
                )
            if err:
                st.error(f"Groq error: {err}")
            else:
                st.session_state.p_slides = data.get("slides", [])
                st.session_state.step = 3
                st.rerun()

    # ── Step 3 ─────────────────────────────────────────────────────────────────
    elif step == 3:
        st.subheader("Step 3 — Review & Download")
        st.success("Slides generated — review them below, then download.")

        for i, slide in enumerate(st.session_state.p_slides):
            with st.expander(f"Slide {i + 2}: {slide['title']}", expanded=(i == 0)):
                st.write(slide["content"])

        st.divider()
        a, b = st.columns(2)
        if a.button("← Regenerate"):
            st.session_state.step = 2
            st.rerun()

        if b.button("📥 Download PowerPoint", type="primary"):
            prs = Presentation()

            # Title slide
            ts = prs.slides.add_slide(prs.slide_layouts[0])
            ts.shapes.title.text    = st.session_state.p_name
            ts.placeholders[1].text = st.session_state.p_tagline

            # Content slides
            for slide in st.session_state.p_slides:
                s = prs.slides.add_slide(prs.slide_layouts[1])
                s.shapes.title.text    = slide["title"]
                s.placeholders[1].text = slide["content"]

            buf = io.BytesIO()
            prs.save(buf)           # no disk write
            buf.seek(0)

            fname = (st.session_state.p_name or "Apex").replace(" ", "_")
            st.download_button(
                label="⬇️  Save Portfolio PPTX",
                data=buf,
                file_name=f"{fname}_Portfolio.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )

# ══════════════════════════════════════════════════════════════════════════════
#  CAREER INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "career":
    st.title("🎯 Career Intelligence")
    st.caption("ATS match score · Skill-gap analysis · AI improvement suggestions")

    tab_ats, tab_jd = st.tabs(["📊  ATS Score Checker", "🔍  JD Analyzer"])

    # ── TAB 1: ATS Score Checker ───────────────────────────────────────────────
    with tab_ats:
        left, right = st.columns(2, gap="large")

        with left:
            st.subheader("Job Description")
            st.session_state.ci_role = st.text_input(
                "Target Role", st.session_state.ci_role,
                placeholder="e.g. Data Scientist at Google")
            st.session_state.ci_jd = st.text_area(
                "Paste JD here", st.session_state.ci_jd, height=260)

        with right:
            st.subheader("Your Resume")
            has_blob = bool(st.session_state.r_blob)
            opts = (
                ["✅  Use Resume Builder output", "Paste manually"]
                if has_blob else ["Paste manually"]
            )
            choice = st.radio("Resume source", opts, index=0)

            if "Paste manually" in choice:
                st.session_state.ci_resume_paste = st.text_area(
                    "Paste resume as plain text",
                    st.session_state.ci_resume_paste, height=200,
                )
                resume_text = st.session_state.ci_resume_paste
            else:
                resume_text = st.session_state.r_blob
                st.info(f"Using resume built for: **{st.session_state.r_name}**")

        st.divider()
        run_btn = st.button(
            "🔍  Run ATS Analysis", type="primary", use_container_width=True
        )

        if run_btn:
            if not st.session_state.ci_jd.strip():
                st.error("Paste a job description first.")
            elif not resume_text.strip():
                st.error("Provide your resume text.")
            else:
                # ── Step 1: Extract JD requirements ───────────────────────────
                with st.spinner("Step 1 / 3  ·  Extracting job requirements..."):
                    jd_data, e1 = gj(
                        system="ATS analyzer. JSON only. Be specific and thorough.",
                        user=(
                            "Extract from this job description:\n"
                            "- required_skills: list of 10–15 specific technical/hard skills required\n"
                            "- preferred_skills: list of 5–8 nice-to-have skills\n"
                            "- key_responsibilities: list of 4–5 core responsibilities (short phrases)\n"
                            "- experience_level: 'junior', 'mid-level', or 'senior'\n"
                            "- domain: e.g. 'Machine Learning', 'Full Stack', 'Data Engineering'\n\n"
                            f"Job Description:\n{st.session_state.ci_jd}\n\n"
                            'Schema: {"required_skills":[],"preferred_skills":[],'
                            '"key_responsibilities":[],"experience_level":"","domain":""}'
                        ),
                    )
                if e1 or not jd_data:
                    st.error(f"JD analysis failed: {e1}")
                    st.stop()

                # ── Step 2: Match resume vs JD ─────────────────────────────────
                with st.spinner("Step 2 / 3  ·  Scanning resume against requirements..."):
                    match_data, e2 = gj(
                        system=(
                            "Strict ATS resume scanner. JSON only. "
                            "Only mark a skill as matched if it clearly appears in the resume."
                        ),
                        user=(
                            "Scan this resume and identify which skills are present.\n\n"
                            f"Resume:\n{resume_text}\n\n"
                            f"Required Skills to check: {jd_data.get('required_skills', [])}\n"
                            f"Preferred Skills to check: {jd_data.get('preferred_skills', [])}\n\n"
                            'Schema: {"matched_required":[],"missing_required":[],'
                            '"matched_preferred":[],"missing_preferred":[]}'
                        ),
                    )
                if e2 or not match_data:
                    st.error(f"Skill matching failed: {e2}")
                    st.stop()

                # ── Step 3: AI improvement suggestions ────────────────────────
                with st.spinner("Step 3 / 3  ·  Generating improvement suggestions..."):
                    sugg, _ = gt(
                        system="Professional resume coach. Be specific, direct, and practical.",
                        user=(
                            f"Write 5 numbered, specific suggestions to improve this resume "
                            f"for {st.session_state.ci_role or 'the target role'}.\n\n"
                            f"Missing required skills: {match_data.get('missing_required', [])}\n"
                            f"Missing preferred skills: {match_data.get('missing_preferred', [])}\n"
                            f"Key responsibilities: {jd_data.get('key_responsibilities', [])}\n"
                            f"Expected level: {jd_data.get('experience_level', '')}\n\n"
                            "For each suggestion: state exactly what to add or rewrite in the resume."
                        ),
                    )

                # ── Compute scores ─────────────────────────────────────────────
                mreq = match_data.get("matched_required",  [])
                xreq = match_data.get("missing_required",  [])
                mpre = match_data.get("matched_preferred", [])
                xpre = match_data.get("missing_preferred", [])
                req  = jd_data.get("required_skills",  [])
                pre  = jd_data.get("preferred_skills", [])

                rs = len(mreq) / max(len(req), 1) * 100
                ps = len(mpre) / max(len(pre), 1) * 100
                ov = rs * 0.75 + ps * 0.25

                st.session_state.ci_result = {
                    "role":  st.session_state.ci_role,
                    "domain": jd_data.get("domain", ""),
                    "exp":   jd_data.get("experience_level", ""),
                    "ov": ov, "rs": rs, "ps": ps,
                    "mreq": mreq, "xreq": xreq,
                    "mpre": mpre, "xpre": xpre,
                    "resp": jd_data.get("key_responsibilities", []),
                    "sugg": sugg or "",
                }
                st.rerun()

        # ── RESULTS PANEL ──────────────────────────────────────────────────────
        if st.session_state.ci_result:
            r = st.session_state.ci_result
            st.divider()

            if r["role"]:
                st.subheader(f"Results: {r['role']}")

            # Role metadata
            meta = st.columns(3)
            if r.get("domain"): meta[0].metric("Domain",           r["domain"])
            if r.get("exp"):    meta[1].metric("Expected Level",   r["exp"].title())

            st.markdown("")

            # Score metrics
            label = (
                "Strong Match 🎯" if r["ov"] >= 70 else
                "Fair Match ⚠️"   if r["ov"] >= 45 else
                "Weak Match ❌"
            )
            s1, s2, s3 = st.columns(3)
            s1.metric("Overall ATS Score",  f"{r['ov']:.0f}%", label)
            s2.metric("Required Skills",    f"{r['rs']:.0f}%",
                      f"{len(r['mreq'])} / {len(r['mreq']) + len(r['xreq'])} matched")
            s3.metric("Preferred Skills",   f"{r['ps']:.0f}%",
                      f"{len(r['mpre'])} / {len(r['mpre']) + len(r['xpre'])} matched")

            st.markdown("")

            # Donut chart + skill chips
            chart_col, skill_col = st.columns([1, 1.5], gap="large")

            with chart_col:
                st.markdown("**Skill Breakdown**")
                if PLOTLY:
                    fig = go.Figure(go.Pie(
                        labels=["Required ✓", "Required ✗",
                                "Preferred ✓", "Preferred ✗"],
                        values=[len(r["mreq"]), len(r["xreq"]),
                                len(r["mpre"]), len(r["xpre"])],
                        hole=0.62,
                        marker_colors=["#10b981", "#ef4444",
                                       "#3b82f6", "#f59e0b"],
                        textinfo="label+value",
                        hovertemplate="%{label}: %{value} skills<extra></extra>",
                    ))
                    fig.update_layout(
                        showlegend=False,
                        margin=dict(t=10, b=10, l=10, r=10),
                        height=260,
                        annotations=[dict(
                            text=f"<b>{r['ov']:.0f}%</b>",
                            x=0.5, y=0.5, font_size=24, showarrow=False,
                        )],
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.metric("Score", f"{r['ov']:.0f}%")

            with skill_col:
                t1, t2 = st.tabs(["✅  Matched", "❌  Missing"])

                with t1:
                    if r["mreq"]:
                        st.markdown("**Required** — found in your resume")
                        st.markdown(chips(r["mreq"], "chip-g"), unsafe_allow_html=True)
                    if r["mpre"]:
                        st.markdown("**Preferred** — found in your resume")
                        st.markdown(chips(r["mpre"], "chip-b"), unsafe_allow_html=True)
                    if not r["mreq"] and not r["mpre"]:
                        st.info("No matches found. Try pasting a more detailed resume.")

                with t2:
                    if r["xreq"]:
                        st.markdown("**Required** — add these first")
                        st.markdown(chips(r["xreq"], "chip-r"), unsafe_allow_html=True)
                    if r["xpre"]:
                        st.markdown("**Preferred** — nice to add")
                        st.markdown(chips(r["xpre"], "chip-y"), unsafe_allow_html=True)
                    if not r["xreq"] and not r["xpre"]:
                        st.success("You matched everything — strong resume for this role!")

            if r.get("resp"):
                with st.expander("📌  Key responsibilities from this JD"):
                    for item in r["resp"]:
                        st.markdown(f"- {item}")

            st.divider()
            st.subheader("💡 AI Improvement Suggestions")
            st.markdown(r["sugg"])

            if st.button("🔄  Clear Results & Run Again"):
                st.session_state.ci_result = None
                st.rerun()

    # ── TAB 2: JD Analyzer ────────────────────────────────────────────────────
    with tab_jd:
        st.subheader("Understand any Job Description in seconds")
        st.caption("Paste any JD to get a structured breakdown — no resume needed.")

        jd_raw = st.text_area(
            "Paste Job Description", height=230,
            placeholder="Paste any job description here to analyze it instantly...",
        )

        if st.button("🔍  Analyze JD", type="primary"):
            if not jd_raw.strip():
                st.error("Paste a job description first.")
            else:
                with st.spinner("Analyzing..."):
                    res, err = gj(
                        system="Career intelligence tool. JSON only.",
                        user=(
                            "Deeply analyze this job description and return:\n"
                            "- role_title: the job title\n"
                            "- company_type: startup / mid-size / enterprise / unknown\n"
                            "- domain: main technical domain (e.g. 'Data Science')\n"
                            "- experience_years: expected years (e.g. '2–4 years')\n"
                            "- hard_skills: list of 8–12 specific technical skills required\n"
                            "- soft_skills: list of 4–6 soft skills mentioned\n"
                            "- red_flags: list of 2–3 vague/concerning phrases if any "
                            "(e.g. 'rockstar', 'wear many hats', 'unlimited PTO')\n"
                            "- summary: 2-sentence plain-English overview of the role\n\n"
                            f"JD:\n{jd_raw}\n\n"
                            'Schema: {"role_title":"","company_type":"","domain":"",'
                            '"experience_years":"","hard_skills":[],"soft_skills":[],'
                            '"red_flags":[],"summary":""}'
                        ),
                    )
                if err or not res:
                    st.error(f"Analysis failed: {err}")
                else:
                    a, b, c, d = st.columns(4)
                    a.metric("Role",        res.get("role_title",      "N/A"))
                    b.metric("Domain",      res.get("domain",          "N/A"))
                    c.metric("Company",     res.get("company_type",    "N/A").title())
                    d.metric("Experience",  res.get("experience_years","N/A"))
                    st.markdown(f"**Summary:** {res.get('summary', '')}")
                    st.divider()

                    sc1, sc2 = st.columns(2)
                    with sc1:
                        st.markdown("**🔧 Technical Skills Required**")
                        for s in res.get("hard_skills", []):
                            st.markdown(f"- `{s}`")
                    with sc2:
                        st.markdown("**🤝 Soft Skills Expected**")
                        for s in res.get("soft_skills", []):
                            st.markdown(f"- {s}")

                    rf = res.get("red_flags", [])
                    if rf:
                        st.warning(f"⚠️  **Watch out for:** {', '.join(rf)}")

# ══════════════════════════════════════════════════════════════════════════════
#  COVER LETTER GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "coverletter":
    st.title("✉️ Cover Letter Generator")
    st.caption("Paste your resume + job description → get a tailored, non-generic cover letter instantly.")
    st.divider()

    col_a, col_b = st.columns(2, gap="large")

    with col_a:
        st.subheader("Your Details")
        st.session_state.cl_your_name = st.text_input(
            "Your Name",
            st.session_state.cl_your_name,
            placeholder="e.g. Vedant Sharma",
        )
        st.session_state.cl_role = st.text_input(
            "Role You're Applying For",
            st.session_state.cl_role,
            placeholder="e.g. Data Scientist",
        )
        st.session_state.cl_company = st.text_input(
            "Company Name",
            st.session_state.cl_company,
            placeholder="e.g. Google",
        )
        st.session_state.cl_jd = st.text_area(
            "Paste Job Description",
            st.session_state.cl_jd,
            height=200,
            placeholder="Paste the full job description here...",
        )

    with col_b:
        st.subheader("Your Resume")
        has_resume = bool(st.session_state.r_blob)
        if has_resume:
            src = st.radio("Resume source", ["✅ Use Resume Builder output", "Paste manually"], index=0)
        else:
            src = st.radio("Resume source", ["Paste manually"], index=0)

        if "Paste manually" in src:
            resume_for_cl = st.text_area(
                "Paste resume as plain text",
                height=280,
                placeholder="Paste your resume text here...",
            )
        else:
            resume_for_cl = st.session_state.r_blob
            st.info(f"Using resume: **{st.session_state.r_name}**")

    st.divider()
    if st.button("⚡ Generate Cover Letter", type="primary", use_container_width=True):
        if not st.session_state.cl_role or not st.session_state.cl_company:
            st.error("Please fill in the role and company name.")
        elif not st.session_state.cl_jd.strip():
            st.error("Please paste the job description.")
        elif not resume_for_cl.strip():
            st.error("Please provide your resume text.")
        else:
            with st.spinner("Writing your cover letter..."):
                output, err = gt(
                    system=(
                        "You are an expert cover letter writer. Write compelling, "
                        "specific, and human-sounding cover letters. Never use generic "
                        "phrases like 'I am writing to express my interest'. Be direct, "
                        "confident, and tie specific resume achievements to specific JD requirements."
                    ),
                    user=(
                        f"Write a professional cover letter for {st.session_state.cl_your_name or 'the candidate'} "
                        f"applying for the role of {st.session_state.cl_role} at {st.session_state.cl_company}.\n\n"
                        f"Job Description:\n{st.session_state.cl_jd}\n\n"
                        f"Candidate Resume:\n{resume_for_cl}\n\n"
                        "Instructions:\n"
                        "- Start with a strong, specific opening line (not 'I am writing to...')\n"
                        "- Paragraph 1: Why this role + company specifically (tie to JD)\n"
                        "- Paragraph 2: 2-3 specific achievements from the resume that match JD requirements\n"
                        "- Paragraph 3: What you'll bring to the team in the first 90 days\n"
                        "- Closing: Confident, direct call to action\n"
                        "- Keep it under 350 words\n"
                        "- Do NOT include placeholders like [Your Address] — write the full letter body only."
                    ),
                )
            if err:
                st.error(f"Error: {err}")
            else:
                st.session_state.cl_output = output

    if st.session_state.cl_output:
        st.divider()
        st.subheader("📄 Your Cover Letter")
        st.markdown(st.session_state.cl_output)
        st.divider()

        # Build downloadable PDF
        if st.button("📥 Download as PDF", type="primary"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_margins(20, 20, 20)
            pdf.set_font("Helvetica", "B", 14)
            name_line = st.session_state.cl_your_name or "Applicant"
            pdf.cell(0, 10, latin(name_line), ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 6,
                     latin(f"Applying for: {st.session_state.cl_role} at {st.session_state.cl_company}"),
                     ln=True)
            pdf.ln(6)
            pdf.set_font("Helvetica", "", 11)
            for line in st.session_state.cl_output.split("\n"):
                pdf.multi_cell(0, 6, latin(line))
            pdf.ln(2)
            fname = (st.session_state.cl_your_name or "Cover").replace(" ", "_")
            st.download_button(
                "⬇️ Save Cover Letter PDF",
                data=pdf.output(),
                file_name=f"{fname}_CoverLetter.pdf",
                mime="application/pdf",
            )

        if st.button("🔄 Generate Another Version"):
            st.session_state.cl_output = ""
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  LINKEDIN GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "linkedin":
    st.title("🔗 LinkedIn Generator")
    st.caption("Turn your resume into a recruiter-optimized LinkedIn headline and About section.")
    st.divider()

    st.subheader("Your Information")
    col1, col2 = st.columns(2, gap="large")

    with col1:
        target_role = st.text_input(
            "Target Role / Job Title",
            placeholder="e.g. Data Scientist, ML Engineer, Software Developer",
        )
        industry = st.text_input(
            "Industry / Domain",
            placeholder="e.g. FinTech, Healthcare AI, E-commerce",
        )

    with col2:
        tone = st.selectbox(
            "Tone",
            ["Professional & Authoritative", "Friendly & Approachable",
             "Bold & Ambitious", "Technical & Precise"],
        )

    has_resume = bool(st.session_state.r_blob)
    if has_resume:
        li_src = st.radio("Resume source", ["✅ Use Resume Builder output", "Paste manually"], index=0)
    else:
        li_src = st.radio("Resume source", ["Paste manually"], index=0)

    if "Paste manually" in li_src:
        resume_for_li = st.text_area(
            "Paste your resume / key highlights",
            height=200,
            placeholder="Paste resume text or just your key skills, achievements, and experience...",
        )
    else:
        resume_for_li = st.session_state.r_blob
        st.info(f"Using resume: **{st.session_state.r_name}**")

    st.divider()
    if st.button("⚡ Generate LinkedIn Content", type="primary", use_container_width=True):
        if not target_role:
            st.error("Please enter your target role.")
        elif not resume_for_li.strip():
            st.error("Please provide your resume or highlights.")
        else:
            with st.spinner("Crafting your LinkedIn presence..."):
                data, err = gj(
                    system=(
                        "You are a LinkedIn personal branding expert. Output JSON only. "
                        "Write content that is human, specific, and avoids LinkedIn clichés "
                        "like 'passionate', 'results-driven', 'synergy', or 'thought leader'."
                    ),
                    user=(
                        f"Create LinkedIn content for someone targeting: {target_role}\n"
                        f"Industry: {industry or 'General Tech'}\n"
                        f"Tone: {tone}\n\n"
                        f"Resume/Background:\n{resume_for_li}\n\n"
                        "Return JSON with:\n"
                        "- headline: A compelling LinkedIn headline under 220 characters "
                        "(use | to separate sections, include role + top skill + value prop)\n"
                        "- about: A 3-paragraph LinkedIn About section (260-300 words). "
                        "Paragraph 1: who you are + what you build. "
                        "Paragraph 2: 2-3 specific achievements with numbers. "
                        "Paragraph 3: what you're looking for + call to action.\n"
                        "- tagline: One punchy sentence (under 60 chars) that captures their brand.\n\n"
                        'Schema: {"headline":"","about":"","tagline":""}'
                    ),
                )
            if err or not data:
                st.error(f"Error: {err}")
            else:
                st.session_state.li_output_headline = data.get("headline", "")
                st.session_state.li_output_about    = data.get("about",    "")
                st.session_state.li_output_summary  = data.get("tagline",  "")

    if st.session_state.li_output_headline:
        st.divider()

        h_col, t_col = st.columns([2, 1], gap="large")
        with h_col:
            st.subheader("🏷️ LinkedIn Headline")
            st.info(st.session_state.li_output_headline)
            char_count = len(st.session_state.li_output_headline)
            st.caption(f"{char_count} / 220 characters")
        with t_col:
            st.subheader("✨ Brand Tagline")
            st.success(st.session_state.li_output_summary)

        st.markdown("")
        st.subheader("👤 LinkedIn About Section")
        st.markdown(st.session_state.li_output_about)
        st.divider()

        # Copy-friendly text block
        with st.expander("📋 Copy-ready text (plain)"):
            combined = (
                f"HEADLINE:\n{st.session_state.li_output_headline}\n\n"
                f"ABOUT:\n{st.session_state.li_output_about}"
            )
            st.code(combined, language=None)

        if st.button("🔄 Regenerate"):
            st.session_state.li_output_headline = ""
            st.session_state.li_output_about    = ""
            st.session_state.li_output_summary  = ""
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  COLD OUTREACH GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "coldoutreach":
    st.title("📨 Cold Outreach Generator")
    st.caption("Personalized LinkedIn DMs and cold emails that don't sound templated.")
    st.divider()

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("Target Details")
        st.session_state.co_role    = st.text_input(
            "Role You're Targeting",
            st.session_state.co_role,
            placeholder="e.g. Data Scientist Intern",
        )
        st.session_state.co_company = st.text_input(
            "Company Name",
            st.session_state.co_company,
            placeholder="e.g. Razorpay",
        )
        st.session_state.co_manager = st.text_input(
            "Hiring Manager / Recipient Name (optional)",
            st.session_state.co_manager,
            placeholder="e.g. Rahul Mehta",
        )
        st.session_state.co_context = st.text_area(
            "Any context about the company or person? (optional)",
            st.session_state.co_context,
            height=120,
            placeholder="e.g. I saw their recent Series B announcement, "
                        "I use their product daily, they're expanding the ML team...",
        )

    with col2:
        st.subheader("Your Background")
        outreach_type = st.selectbox(
            "Message Type",
            ["LinkedIn DM (short · under 300 chars)",
             "LinkedIn Note (medium · under 600 chars)",
             "Cold Email (full · with subject line)"],
        )
        has_resume = bool(st.session_state.r_blob)
        if has_resume:
            co_src = st.radio("Your info source",
                              ["✅ Use Resume Builder output", "Paste manually"], index=0)
        else:
            co_src = st.radio("Your info source", ["Paste manually"], index=0)

        if "Paste manually" in co_src:
            resume_for_co = st.text_area(
                "Your key skills / achievements",
                height=200,
                placeholder="e.g. 3rd year CS student, built a churn prediction model, "
                            "Python/ML/SQL, internship at XYZ...",
            )
        else:
            resume_for_co = st.session_state.r_blob
            st.info(f"Using resume: **{st.session_state.r_name}**")

    st.divider()
    if st.button("⚡ Generate Outreach Message", type="primary", use_container_width=True):
        if not st.session_state.co_role or not st.session_state.co_company:
            st.error("Please fill in the role and company.")
        elif not resume_for_co.strip():
            st.error("Please provide your background or resume.")
        else:
            is_email = "Cold Email" in outreach_type
            char_note = (
                "under 300 characters — extremely short and punchy"  if "DM" in outreach_type else
                "under 600 characters — concise but with one key achievement" if "Note" in outreach_type else
                "a full professional email with a subject line"
            )

            with st.spinner("Writing your outreach message..."):
                output, err = gt(
                    system=(
                        "You are an expert at cold outreach that actually gets replies. "
                        "Never use templates, buzzwords, or phrases like 'I hope this message finds you well', "
                        "'I wanted to reach out', or 'I am a big fan'. Be specific, human, and direct."
                    ),
                    user=(
                        f"Write a {outreach_type} from a candidate to "
                        f"{st.session_state.co_manager or 'the hiring team'} at {st.session_state.co_company} "
                        f"about the {st.session_state.co_role} role.\n\n"
                        f"Candidate background:\n{resume_for_co}\n\n"
                        f"Context about company/person:\n{st.session_state.co_context or 'None provided'}\n\n"
                        f"Requirements:\n"
                        f"- Length: {char_note}\n"
                        f"- Open with something specific to them or the company (not a compliment)\n"
                        f"- Mention ONE specific achievement from the candidate that's relevant\n"
                        f"- End with a low-friction ask (not 'Can we jump on a call?')\n"
                        + ("- Include a subject line on the first line as 'Subject: ...'\n" if is_email else "")
                        + "- Write the message only, no commentary or labels."
                    ),
                )
            if err:
                st.error(f"Error: {err}")
            else:
                st.session_state.co_output = output

    if st.session_state.co_output:
        st.divider()
        st.subheader(f"📨 Your {outreach_type.split('(')[0].strip()}")

        msg = st.session_state.co_output
        char_count = len(msg)

        st.markdown(msg)
        st.caption(f"Character count: **{char_count}**")

        with st.expander("📋 Copy-ready (plain text)"):
            st.code(msg, language=None)

        c1, c2 = st.columns(2)
        if c1.button("🔄 Generate Another Version"):
            st.session_state.co_output = ""
            st.rerun()
        if c2.button("✉️ Generate Cover Letter from this →"):
            st.session_state.cl_role    = st.session_state.co_role
            st.session_state.cl_company = st.session_state.co_company
            st.session_state.page       = "coverletter"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  SALARY ESTIMATOR
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "salary":
    st.title("💰 Salary Intelligence Estimator")
    st.caption("Know your market worth — realistic salary range based on role, experience, skills, and location.")
    st.divider()

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("Role & Experience")
        st.session_state.sal_role = st.text_input(
            "Job Title / Role",
            st.session_state.sal_role,
            placeholder="e.g. Data Scientist, ML Engineer, Backend Developer",
        )
        st.session_state.sal_exp = st.select_slider(
            "Years of Experience",
            options=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10+"],
            value=st.session_state.sal_exp,
        )
        st.session_state.sal_location = st.text_input(
            "Location / City",
            st.session_state.sal_location,
            placeholder="e.g. Mumbai, Bangalore, Remote India, San Francisco",
        )

    with col2:
        st.subheader("Skills & Context")
        st.session_state.sal_skills = st.text_area(
            "Your Key Skills",
            st.session_state.sal_skills,
            height=100,
            placeholder="e.g. Python, TensorFlow, MLOps, AWS, SQL, Spark",
        )
        company_type = st.selectbox(
            "Target Company Type",
            ["Any", "Startup (Series A-B)", "Mid-size (500-5000 employees)",
             "Enterprise / MNC", "FAANG / Top Tech", "Government / PSU"],
        )
        education = st.selectbox(
            "Highest Education",
            ["B.Tech / B.E.", "M.Tech / M.S.", "MBA", "BCA / B.Sc",
             "MCA / M.Sc", "PhD", "Diploma / Other"],
        )

    st.divider()
    if st.button("💰 Estimate My Salary", type="primary", use_container_width=True):
        if not st.session_state.sal_role:
            st.error("Please enter your target role.")
        elif not st.session_state.sal_location:
            st.error("Please enter your location.")
        else:
            with st.spinner("Analyzing market data..."):
                data, err = gj(
                    system=(
                        "You are a compensation intelligence expert with deep knowledge of "
                        "tech industry salaries in India and globally. Output JSON only. "
                        "Give realistic, current market data — not aspirational numbers."
                    ),
                    user=(
                        f"Estimate salary for:\n"
                        f"Role: {st.session_state.sal_role}\n"
                        f"Experience: {st.session_state.sal_exp} years\n"
                        f"Location: {st.session_state.sal_location}\n"
                        f"Skills: {st.session_state.sal_skills or 'Not specified'}\n"
                        f"Company type: {company_type}\n"
                        f"Education: {education}\n\n"
                        "Return JSON with:\n"
                        "- min_salary: minimum realistic CTC (string with currency, e.g. '₹6 LPA' or '$90,000')\n"
                        "- max_salary: maximum realistic CTC\n"
                        "- median_salary: most likely CTC for this profile\n"
                        "- currency: 'INR' or 'USD' based on location\n"
                        "- factors_positive: list of 3-4 things about this profile that push salary UP\n"
                        "- factors_negative: list of 2-3 things that pull salary DOWN\n"
                        "- negotiation_tips: list of 3 specific, practical salary negotiation tips "
                        "for this exact role/level\n"
                        "- market_insight: 2-sentence insight about demand/supply for this role right now\n\n"
                        'Schema: {"min_salary":"","max_salary":"","median_salary":"",'
                        '"currency":"","factors_positive":[],"factors_negative":[],'
                        '"negotiation_tips":[],"market_insight":""}'
                    ),
                )
            if err or not data:
                st.error(f"Error: {err}")
            else:
                st.session_state.sal_result = data

    if st.session_state.sal_result:
        r = st.session_state.sal_result
        st.divider()
        st.subheader(f"💰 Salary Range: {st.session_state.sal_role}")

        # Main salary metrics
        s1, s2, s3 = st.columns(3)
        s1.metric("Minimum",  r.get("min_salary",    "N/A"))
        s2.metric("Median ⭐",r.get("median_salary", "N/A"), "Most likely for your profile")
        s3.metric("Maximum",  r.get("max_salary",    "N/A"))

        st.markdown("")

        # Salary bar chart
        if PLOTLY:
            try:
                import re
                def parse_salary(s):
                    nums = re.findall(r"[\d.]+", str(s).replace(",", ""))
                    return float(nums[0]) if nums else 0

                vals  = [
                    parse_salary(r.get("min_salary",    0)),
                    parse_salary(r.get("median_salary", 0)),
                    parse_salary(r.get("max_salary",    0)),
                ]
                unit  = "LPA" if r.get("currency","INR") == "INR" else "K USD"
                fig   = go.Figure(go.Bar(
                    x=["Minimum", "Median", "Maximum"],
                    y=vals,
                    marker_color=["#94a3b8", "#3b82f6", "#10b981"],
                    text=[r.get("min_salary",""), r.get("median_salary",""), r.get("max_salary","")],
                    textposition="outside",
                ))
                fig.update_layout(
                    yaxis_title=unit,
                    height=280,
                    margin=dict(t=20, b=20, l=20, r=20),
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass  # chart is optional — metrics above are the core output

        st.divider()
        fc1, fc2 = st.columns(2)
        with fc1:
            st.markdown("**📈 What's pushing your salary UP**")
            for f in r.get("factors_positive", []):
                st.markdown(f"- 🟢 {f}")
        with fc2:
            st.markdown("**📉 What's pulling your salary DOWN**")
            for f in r.get("factors_negative", []):
                st.markdown(f"- 🔴 {f}")

        st.divider()
        st.subheader("🤝 Negotiation Tips")
        for tip in r.get("negotiation_tips", []):
            st.markdown(f"- 💡 {tip}")

        if r.get("market_insight"):
            st.info(f"📊 **Market Insight:** {r['market_insight']}")

        if st.button("🔄 Recalculate"):
            st.session_state.sal_result = None
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  MOCK INTERVIEWER
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "interview":
    st.title("🎤 Mock Interviewer")
    st.caption("AI-powered practice — real questions, per-answer scoring, full PDF report.")
    st.divider()

    # ── SETUP PHASE ────────────────────────────────────────────────────────────
    if not st.session_state.mi_setup_done:
        st.subheader("Interview Setup")
        col1, col2 = st.columns(2, gap="large")

        with col1:
            st.session_state.mi_role = st.text_input(
                "Target Role *", st.session_state.mi_role,
                placeholder="e.g. Data Scientist, ML Engineer, Software Developer",
            )
            mi_type = st.selectbox(
                "Interview Type",
                ["Mixed (Technical + Behavioral)", "Technical Only",
                 "Behavioral / HR Only"],
            )
            mi_difficulty = st.selectbox(
                "Difficulty Level",
                ["Easy (Fresher / Entry-level)",
                 "Medium (1-3 years)",
                 "Hard (Senior / FAANG)"],
            )
            mi_num_q = st.selectbox("Number of Questions", [5, 8, 10], index=1)

        with col2:
            st.session_state.mi_jd = st.text_area(
                "Job Description (optional — makes questions role-specific)",
                st.session_state.mi_jd, height=150,
                placeholder="Paste the JD here for tailored questions...",
            )
            has_resume = bool(st.session_state.r_blob)
            if has_resume:
                mi_src = st.radio("Your background source",
                                  ["✅ Use Resume Builder output", "Paste manually"],
                                  index=0)
            else:
                mi_src = st.radio("Your background source", ["Paste manually"], index=0)

            if "Paste manually" in mi_src:
                mi_resume = st.text_area(
                    "Your resume / key skills & experience",
                    height=150,
                    placeholder="Paste so questions match your actual background...",
                )
            else:
                mi_resume = st.session_state.r_blob
                st.info(f"Using resume: **{st.session_state.r_name}**")

        st.divider()
        if st.button("🎤 Generate Questions & Start", type="primary",
                     use_container_width=True):
            if not st.session_state.mi_role.strip():
                st.error("Please enter your target role.")
            else:
                with st.spinner("Generating your personalised interview questions..."):
                    q_data, err = gj(
                        system=(
                            "You are a senior technical interviewer at a top tech company. "
                            "Generate realistic, specific interview questions. "
                            "Never use generic filler questions. Output JSON only."
                        ),
                        user=(
                            f"Generate exactly {mi_num_q} interview questions for: "
                            f"{st.session_state.mi_role}\n"
                            f"Interview type: {mi_type}\n"
                            f"Difficulty: {mi_difficulty}\n"
                            f"JD context: {st.session_state.mi_jd or 'Not provided'}\n"
                            f"Candidate background: {mi_resume or 'Not provided'}\n\n"
                            "Rules:\n"
                            "- Mixed: ~60% Technical, ~40% Behavioral\n"
                            "- Technical Only: all problem-solving / concept questions\n"
                            "- Behavioral: all STAR-method situational questions\n"
                            "- Make every question specific to this role — not generic\n"
                            "- For each question include a one-sentence hint of what "
                            "a strong answer covers\n\n"
                            'Schema: {"questions":[{"q":"","category":"Technical" or '
                            '"Behavioral","hint":""}]}'
                        ),
                    )
                if err or not q_data or not q_data.get("questions"):
                    st.error(f"Could not generate questions: {err}")
                else:
                    qs = q_data["questions"]
                    st.session_state.mi_questions      = qs
                    st.session_state.mi_answers        = [""] * len(qs)
                    st.session_state.mi_scores         = [None] * len(qs)
                    st.session_state.mi_current_q      = 0
                    st.session_state.mi_interview_done = False
                    st.session_state.mi_report         = None
                    st.session_state.mi_setup_done     = True
                    st.rerun()

    # ── INTERVIEW PHASE ────────────────────────────────────────────────────────
    elif st.session_state.mi_setup_done and not st.session_state.mi_interview_done:
        questions = st.session_state.mi_questions
        curr_idx  = st.session_state.mi_current_q
        total_q   = len(questions)

        # Progress bar
        st.progress(curr_idx / total_q, text=f"Question {curr_idx + 1} of {total_q}")
        b1, b2 = st.columns(2)
        b1.caption(f"Role: **{st.session_state.mi_role}**")
        b2.caption(f"Completed: **{curr_idx} / {total_q}**")
        st.divider()

        curr_q = questions[curr_idx]
        cat    = curr_q.get("category", "General")
        cat_icon = "🔵" if cat == "Technical" else "🟠"

        # Question display
        st.markdown(f"### {cat_icon} Q{curr_idx + 1} — {curr_q['q']}")
        st.caption(f"Category: **{cat}**")

        with st.expander("💡 Hint — what a strong answer covers"):
            st.info(curr_q.get("hint",
                    "Use specific examples, quantify outcomes where possible."))

        st.markdown("")
        answer = st.text_area(
            "Your Answer",
            height=200,
            placeholder=(
                "Behavioral → STAR method: Situation · Task · Action · Result\n"
                "Technical  → Explain your reasoning, not just the final answer."
            ),
            key=f"ans_{curr_idx}",
        )

        c_sub, c_skip, c_end = st.columns([2, 1, 1])
        submitted = c_sub.button("✅ Submit Answer", type="primary",
                                 use_container_width=True)
        skipped   = c_skip.button("⏭️ Skip", use_container_width=True)
        ended     = c_end.button("🏁 End Early", use_container_width=True)

        # ── Submit or skip ─────────────────────────────────────────────────────
        if submitted or skipped:
            final_ans = answer.strip() if submitted else "[Skipped]"
            if submitted and not final_ans:
                st.error("Please type an answer before submitting.")
            else:
                if final_ans == "[Skipped]":
                    sc = {
                        "score": 0,
                        "feedback": "Question skipped — no score awarded.",
                        "strengths": [],
                        "improvements": [
                            "Practice answering this — skipped questions are real gaps."
                        ],
                        "model_answer_hint": curr_q.get("hint", ""),
                    }
                else:
                    with st.spinner("Evaluating your answer..."):
                        sc, err = gj(
                            system=(
                                "You are a strict but fair interview evaluator. "
                                "Score answers honestly: average = 5-6, good = 7-8, "
                                "excellent = 9-10. Output JSON only."
                            ),
                            user=(
                                f"Role: {st.session_state.mi_role}\n"
                                f"Question: {curr_q['q']}\n"
                                f"Category: {cat}\n"
                                f"Candidate answer: {final_ans}\n\n"
                                "Return JSON:\n"
                                "- score: integer 1-10\n"
                                "- feedback: 2-3 sentences overall\n"
                                "- strengths: list of 2-3 specific things done well\n"
                                "- improvements: list of 2-3 specific things to improve\n"
                                "- model_answer_hint: 1-2 sentences on what an ideal "
                                "answer would include\n\n"
                                'Schema: {"score":0,"feedback":"","strengths":[],'
                                '"improvements":[],"model_answer_hint":""}'
                            ),
                        )
                    if err or not sc:
                        sc = {
                            "score": 5, "feedback": "Answer recorded.",
                            "strengths": [], "improvements": [],
                            "model_answer_hint": "",
                        }

                st.session_state.mi_answers[curr_idx] = final_ans
                st.session_state.mi_scores[curr_idx]  = sc

                if curr_idx + 1 >= total_q:
                    st.session_state.mi_interview_done = True
                else:
                    st.session_state.mi_current_q = curr_idx + 1
                st.rerun()

        # ── End early ──────────────────────────────────────────────────────────
        if ended:
            for i in range(curr_idx, total_q):
                if not st.session_state.mi_answers[i]:
                    st.session_state.mi_answers[i] = "[Skipped]"
                    st.session_state.mi_scores[i]  = {
                        "score": 0, "feedback": "Skipped.",
                        "strengths": [], "improvements": [],
                        "model_answer_hint": "",
                    }
            st.session_state.mi_interview_done = True
            st.rerun()

        # ── Show previous answer feedback ──────────────────────────────────────
        if curr_idx > 0:
            prev = st.session_state.mi_scores[curr_idx - 1]
            if prev:
                st.divider()
                with st.expander(
                    f"📊 Feedback on Q{curr_idx} — Score: {prev['score']}/10",
                    expanded=False,
                ):
                    sv = prev["score"]
                    icon = "🟢" if sv >= 8 else ("🟡" if sv >= 5 else "🔴")
                    st.markdown(f"**{icon} Score: {sv} / 10**")
                    st.markdown(prev.get("feedback", ""))
                    if prev.get("strengths"):
                        st.markdown("**✅ Strengths:**")
                        for x in prev["strengths"]:
                            st.markdown(f"- {x}")
                    if prev.get("improvements"):
                        st.markdown("**📈 Improve:**")
                        for x in prev["improvements"]:
                            st.markdown(f"- {x}")
                    if prev.get("model_answer_hint"):
                        st.info(f"💡 Ideal answer covers: {prev['model_answer_hint']}")

        st.divider()
        if st.button("🔄 Restart Interview"):
            for k in ["mi_setup_done","mi_questions","mi_current_q",
                      "mi_answers","mi_scores","mi_interview_done","mi_report"]:
                st.session_state[k] = [] if k in ("mi_questions","mi_answers",
                                                    "mi_scores") else (
                    False if isinstance(st.session_state[k], bool) else
                    0      if isinstance(st.session_state[k], int)  else None
                )
            st.session_state.mi_setup_done = False
            st.rerun()

    # ── REPORT PHASE ───────────────────────────────────────────────────────────
    elif st.session_state.mi_interview_done:
        questions = st.session_state.mi_questions
        scores    = st.session_state.mi_scores
        answers   = st.session_state.mi_answers

        # Generate report once
        if not st.session_state.mi_report:
            with st.spinner("Generating your full interview report..."):
                qa_block = "\n\n".join(
                    f"Q{i+1} [{q.get('category','')}]: {q['q']}\n"
                    f"Answer: {answers[i]}\n"
                    f"Score: {(scores[i] or {}).get('score', 0)}/10"
                    for i, q in enumerate(questions)
                )
                rep_data, err = gj(
                    system=(
                        "You are a senior career coach. Provide honest, specific, "
                        "constructive interview performance analysis. Output JSON only."
                    ),
                    user=(
                        f"Analyze this mock interview for: {st.session_state.mi_role}\n\n"
                        f"{qa_block}\n\n"
                        "Return JSON:\n"
                        "- overall_score: integer 1-100\n"
                        "- readiness_label: 'Not Ready' / 'Needs Work' / "
                        "'Almost There' / 'Interview Ready'\n"
                        "- overall_feedback: 3-4 sentence honest assessment\n"
                        "- top_strengths: list of 3 specific strengths shown\n"
                        "- critical_gaps: list of 3 specific weaknesses to fix\n"
                        "- study_topics: list of 5 specific topics/skills to study\n"
                        "- next_steps: list of 3 concrete actions for the next 7 days\n\n"
                        'Schema: {"overall_score":0,"readiness_label":"",'
                        '"overall_feedback":"","top_strengths":[],'
                        '"critical_gaps":[],"study_topics":[],"next_steps":[]}'
                    ),
                )
                if err or not rep_data:
                    valid = [s["score"] for s in scores if s and s.get("score", 0) > 0]
                    avg   = sum(valid) / max(len(valid), 1) if valid else 0
                    rep_data = {
                        "overall_score": int(avg * 10),
                        "readiness_label": "Needs Work" if avg < 6 else "Almost There",
                        "overall_feedback": (
                            "Interview complete. Review per-question feedback below."
                        ),
                        "top_strengths": [], "critical_gaps": [],
                        "study_topics": [], "next_steps": [],
                    }
                st.session_state.mi_report = rep_data
                st.rerun()

        rep     = st.session_state.mi_report
        overall = rep.get("overall_score", 0)
        label   = rep.get("readiness_label", "")
        badge   = "🟢" if overall >= 75 else ("🟡" if overall >= 50 else "🔴")

        st.subheader(f"📊 Interview Report — {st.session_state.mi_role}")

        # Top-level metrics
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Overall Score",  f"{overall} / 100")
        sc2.metric("Readiness",      f"{badge} {label}")
        valid_sc = [s["score"] for s in scores if s and s.get("score", 0) > 0]
        sc3.metric("Avg Answer",
                   f"{sum(valid_sc)/len(valid_sc):.1f} / 10" if valid_sc else "N/A")

        st.markdown("")
        st.markdown(rep.get("overall_feedback", ""))
        st.divider()

        # Per-question score chart
        if PLOTLY:
            q_labels  = [f"Q{i+1}" for i in range(len(questions))]
            q_scores  = [(s or {}).get("score", 0) for s in scores]
            bar_clrs  = [
                "#10b981" if s >= 8 else ("#f59e0b" if s >= 5 else "#ef4444")
                for s in q_scores
            ]
            fig = go.Figure(go.Bar(
                x=q_labels, y=q_scores,
                marker_color=bar_clrs,
                text=q_scores, textposition="outside",
            ))
            fig.update_layout(
                yaxis=dict(range=[0, 11], title="Score / 10"),
                height=280,
                margin=dict(t=30, b=20, l=20, r=20),
                plot_bgcolor="rgba(0,0,0,0)",
                title_text="Per-Question Scores",
            )
            st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # Strengths + Gaps
        sg1, sg2 = st.columns(2)
        with sg1:
            st.markdown("**💪 Top Strengths**")
            for s in rep.get("top_strengths", []):
                st.markdown(f"- 🟢 {s}")
        with sg2:
            st.markdown("**⚠️ Critical Gaps**")
            for g in rep.get("critical_gaps", []):
                st.markdown(f"- 🔴 {g}")

        st.divider()

        # Study plan + next steps
        sp1, sp2 = st.columns(2)
        with sp1:
            st.markdown("**📚 Study Before Your Next Interview**")
            for t in rep.get("study_topics", []):
                st.markdown(f"- 📖 `{t}`")
        with sp2:
            st.markdown("**✅ Your 7-Day Action Plan**")
            for n in rep.get("next_steps", []):
                st.markdown(f"- 🎯 {n}")

        st.divider()

        # Full Q&A detail
        st.subheader("📋 Detailed Q&A Review")
        for i, (q, a, sc) in enumerate(zip(questions, answers, scores)):
            sv   = (sc or {}).get("score", 0)
            icon = "🟢" if sv >= 8 else ("🟡" if sv >= 5 else "🔴")
            with st.expander(
                f"{icon} Q{i+1} [{q.get('category','')}] — "
                f"{q['q'][:65]}... | Score {sv}/10",
                expanded=False,
            ):
                st.markdown(f"**Question:** {q['q']}")
                st.markdown(f"**Your Answer:** {a}")
                if sc:
                    st.markdown(f"**Score: {sv} / 10**")
                    st.markdown(f"**Feedback:** {sc.get('feedback','')}")
                    if sc.get("strengths"):
                        st.markdown("**✅ What you did well:**")
                        for x in sc["strengths"]:
                            st.markdown(f"  - {x}")
                    if sc.get("improvements"):
                        st.markdown("**📈 What to improve:**")
                        for x in sc["improvements"]:
                            st.markdown(f"  - {x}")
                    if sc.get("model_answer_hint"):
                        st.info(f"💡 Ideal answer covers: {sc['model_answer_hint']}")

        st.divider()

        # ── PDF Report ─────────────────────────────────────────────────────────
        if st.button("📥 Download Full Report PDF", type="primary"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_margins(15, 15, 15)

            # Header
            pdf.set_font("Helvetica", "B", 20)
            pdf.cell(0, 12, latin("MOCK INTERVIEW REPORT"), align="C", ln=True)
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 7, latin(f"Role: {st.session_state.mi_role}"),
                     align="C", ln=True)
            pdf.ln(4)

            # Summary
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 8, latin(f"Overall Score: {overall}/100  —  {label}"), ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 5, latin(rep.get("overall_feedback", "")))
            pdf.ln(4)

            # Strengths
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "TOP STRENGTHS", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for s in rep.get("top_strengths", []):
                pdf.multi_cell(0, 5, latin(f"+ {s}"))
            pdf.ln(3)

            # Gaps
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "CRITICAL GAPS", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for g in rep.get("critical_gaps", []):
                pdf.multi_cell(0, 5, latin(f"- {g}"))
            pdf.ln(3)

            # Study plan
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "7-DAY STUDY PLAN", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for t in rep.get("study_topics", []):
                pdf.multi_cell(0, 5, latin(f"* {t}"))
            pdf.ln(4)

            # Q&A detail
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 8, "DETAILED Q&A REVIEW", ln=True)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(3)

            for i, (q, a, sc) in enumerate(zip(questions, answers, scores)):
                sv = (sc or {}).get("score", 0)
                pdf.set_font("Helvetica", "B", 11)
                pdf.multi_cell(
                    0, 6,
                    latin(f"Q{i+1} [{q.get('category','')}] — Score: {sv}/10"),
                )
                pdf.set_font("Helvetica", "I", 10)
                pdf.multi_cell(0, 5, latin(q["q"]))
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(0, 5, latin(f"Answer: {a}"))
                if sc:
                    pdf.multi_cell(0, 5, latin(f"Feedback: {sc.get('feedback','')}"))
                pdf.ln(3)

            fname = (
                st.session_state.r_name or st.session_state.mi_role or "Interview"
            ).replace(" ", "_")
            st.download_button(
                "⬇️ Save Report PDF",
                data=pdf.output(),
                file_name=f"{fname}_InterviewReport.pdf",
                mime="application/pdf",
            )

        if st.button("🔄 Start New Interview"):
            st.session_state.mi_setup_done     = False
            st.session_state.mi_questions      = []
            st.session_state.mi_current_q      = 0
            st.session_state.mi_answers        = []
            st.session_state.mi_scores         = []
            st.session_state.mi_interview_done = False
            st.session_state.mi_report         = None
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  APPLICATION TRACKER
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "tracker":
    st.title("📋 Application Tracker")
    st.caption("Log every application · Kanban board · AI follow-up emails · Analytics")
    st.divider()

    tab_board, tab_add, tab_stats = st.tabs(
        ["📌  Kanban Board", "➕  Add Application", "📊  Analytics"]
    )

    # ── TAB 1: KANBAN BOARD ────────────────────────────────────────────────────
    with tab_board:
        apps = at_all()

        if not apps:
            st.info(
                "No applications yet — head to the **Add Application** tab "
                "to log your first one."
            )
        else:
            # Quick summary strip
            total    = len(apps)
            offers   = sum(1 for a in apps if a["status"] == "Offer 🎉")
            active   = sum(
                1 for a in apps if a["status"] not in ("Offer 🎉", "Rejected")
            )
            rejected = sum(1 for a in apps if a["status"] == "Rejected")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Applied",  total)
            m2.metric("Active",         active)
            m3.metric("Offers",         offers)
            m4.metric("Success Rate",
                      f"{offers / total * 100:.0f}%" if total else "0%")
            st.markdown("")

            # Kanban columns — one per status
            k_cols = st.columns(len(AT_STATUSES), gap="small")
            for col, status in zip(k_cols, AT_STATUSES):
                bucket = [a for a in apps if a["status"] == status]
                color  = AT_COLORS.get(status, "#64748b")

                col.markdown(
                    f"<div style='background:{color};color:white;padding:5px 8px;"
                    f"border-radius:8px;text-align:center;font-weight:700;"
                    f"font-size:0.72rem;margin-bottom:6px;'>"
                    f"{status} ({len(bucket)})</div>",
                    unsafe_allow_html=True,
                )

                for app in bucket:
                    with col.expander(f"🏢 {app['company']}", expanded=False):
                        st.markdown(f"**Role:** {app['role']}")
                        if app.get("date_applied"):
                            st.caption(f"📅 Applied: {app['date_applied']}")
                        if app.get("salary_range"):
                            st.caption(f"💰 {app['salary_range']}")
                        if app.get("contact"):
                            st.caption(f"👤 {app['contact']}")
                        if app.get("jd_url"):
                            st.markdown(f"[🔗 View JD]({app['jd_url']})")
                        if app.get("notes"):
                            st.markdown(f"📝 {app['notes']}")
                        if app.get("next_action"):
                            st.info(f"**Next:** {app['next_action']}")

                        # Move status
                        new_st = st.selectbox(
                            "Move to stage",
                            AT_STATUSES,
                            index=AT_STATUSES.index(status),
                            key=f"st_{app['id']}",
                        )
                        if new_st != status:
                            at_set_status(app["id"], new_st)
                            st.rerun()

                        # Edit notes & next action
                        upd_notes = st.text_area(
                            "Notes", app.get("notes", ""),
                            height=70, key=f"n_{app['id']}",
                        )
                        upd_next = st.text_input(
                            "Next action", app.get("next_action", ""),
                            key=f"nx_{app['id']}",
                        )

                        b1, b2, b3 = st.columns(3)

                        if b1.button("💾", key=f"sv_{app['id']}",
                                     help="Save notes"):
                            at_save_notes(app["id"], upd_notes, upd_next)
                            st.success("Saved!")
                            st.rerun()

                        if b2.button("🗑️", key=f"dl_{app['id']}",
                                     help="Delete this application"):
                            at_delete(app["id"])
                            st.rerun()

                        # AI follow-up email
                        if b3.button("✉️", key=f"fu_{app['id']}",
                                     help="Generate AI follow-up email"):
                            with st.spinner("Writing follow-up..."):
                                fu, _ = gt(
                                    system=(
                                        "You are a professional email writer. "
                                        "Write concise, specific follow-up emails. "
                                        "No clichés, no templates."
                                    ),
                                    user=(
                                        f"Write a brief follow-up email for:\n"
                                        f"Company: {app['company']}\n"
                                        f"Role: {app['role']}\n"
                                        f"Current stage: {app['status']}\n"
                                        f"Applied: {app.get('date_applied','unknown')}\n"
                                        f"Contact: {app.get('contact','Hiring Team')}\n"
                                        f"Notes: {app.get('notes','')}\n\n"
                                        "Rules: under 120 words, include subject line, "
                                        "specific to the current stage, direct call to action."
                                    ),
                                )
                            if fu:
                                st.markdown("**📧 Follow-up Draft:**")
                                st.code(fu, language=None)

    # ── TAB 2: ADD APPLICATION ─────────────────────────────────────────────────
    with tab_add:
        st.subheader("Log a New Application")
        a1, a2 = st.columns(2, gap="large")

        with a1:
            add_company = st.text_input(
                "Company Name *", placeholder="e.g. Google"
            )
            add_role = st.text_input(
                "Role Applied For *", placeholder="e.g. Data Scientist"
            )
            add_status = st.selectbox("Current Status", AT_STATUSES)
            add_date   = st.date_input(
                "Date Applied", value=datetime.date.today()
            )

        with a2:
            add_salary  = st.text_input(
                "Expected Salary / Range", placeholder="e.g. ₹12–15 LPA"
            )
            add_contact = st.text_input(
                "Recruiter / Contact Name", placeholder="e.g. Priya Sharma"
            )
            add_jd_url  = st.text_input(
                "JD URL (optional)", placeholder="https://..."
            )
            add_next    = st.text_input(
                "Next Action", placeholder="e.g. Follow up on Friday"
            )

        add_notes = st.text_area(
            "Notes", height=100,
            placeholder="Interview feedback, preparation notes, red flags...",
        )

        st.divider()
        if st.button("➕  Add Application", type="primary",
                     use_container_width=True):
            if not add_company.strip() or not add_role.strip():
                st.error("Company name and role are required.")
            else:
                at_add(
                    company      = add_company.strip(),
                    role         = add_role.strip(),
                    status       = add_status,
                    date_applied = str(add_date),
                    jd_url       = add_jd_url.strip(),
                    notes        = add_notes.strip(),
                    salary_range = add_salary.strip(),
                    contact      = add_contact.strip(),
                    next_action  = add_next.strip(),
                )
                st.success(
                    f"✅ Logged: **{add_role}** at **{add_company}** — "
                    f"check the Kanban board."
                )

    # ── TAB 3: ANALYTICS ───────────────────────────────────────────────────────
    with tab_stats:
        apps = at_all()

        if not apps:
            st.info("Add applications first to see your analytics.")
        else:
            st.subheader("📊 Your Job Search Analytics")
            total    = len(apps)
            by_st    = {s: sum(1 for a in apps if a["status"] == s)
                        for s in AT_STATUSES}
            offers   = by_st.get("Offer 🎉", 0)
            rejected = by_st.get("Rejected", 0)
            active   = total - offers - rejected
            replied  = total - rejected

            # Headline metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Applied",   total)
            m2.metric("Active Pipeline", active)
            m3.metric("Offers",          offers)
            m4.metric("Response Rate",
                      f"{replied / total * 100:.0f}%" if total else "0%")

            st.markdown("")

            # Funnel bar chart
            if PLOTLY:
                fig = go.Figure(go.Bar(
                    x=list(by_st.keys()),
                    y=list(by_st.values()),
                    marker_color=list(AT_COLORS.values()),
                    text=list(by_st.values()),
                    textposition="outside",
                ))
                fig.update_layout(
                    title_text="Applications by Stage",
                    height=300,
                    margin=dict(t=40, b=20, l=20, r=20),
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig, use_container_width=True)

            # Top companies + recent timeline
            from collections import Counter
            top_cos = Counter(a["company"] for a in apps).most_common(5)

            cl, cr = st.columns(2)
            with cl:
                st.markdown("**🏢 Most Applied Companies**")
                for co, cnt in top_cos:
                    st.markdown(f"- **{co}** — {cnt} application(s)")

            with cr:
                st.markdown("**📅 Recent Applications**")
                recent = sorted(
                    apps,
                    key=lambda x: x.get("date_applied", ""),
                    reverse=True,
                )[:8]
                for a in recent:
                    color = AT_COLORS.get(a["status"], "#64748b")
                    st.markdown(
                        f"- **{a['company']}** · {a['role']} "
                        f"<span style='background:{color};color:white;"
                        f"padding:2px 7px;border-radius:99px;font-size:0.72rem;'>"
                        f"{a['status']}</span>",
                        unsafe_allow_html=True,
                    )

# ══════════════════════════════════════════════════════════════════════════════
#  SKILL-GAP LEARNING ROADMAP
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "roadmap":
    st.title("📚 Skill-Gap Learning Roadmap")
    st.caption("Turn missing skills into a structured week-by-week plan — with free resources and mini-projects.")
    st.divider()

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("What do you need to learn?")
        st.session_state.sg_role = st.text_input(
            "Target Role", st.session_state.sg_role,
            placeholder="e.g. Data Scientist, ML Engineer, DevOps",
        )
        # Pull missing skills from ATS if available
        has_ats = bool(
            st.session_state.ci_result
            and st.session_state.ci_result.get("xreq")
        )
        if has_ats:
            ats_missing = (
                st.session_state.ci_result["xreq"]
                + st.session_state.ci_result.get("xpre", [])
            )
            sg_src = st.radio(
                "Skills source",
                ["✅ Use missing skills from ATS Checker", "Enter manually"],
                index=0,
            )
        else:
            sg_src = "Enter manually"
            st.radio("Skills source", ["Enter manually"], index=0)

        if "Enter manually" in sg_src:
            st.session_state.sg_skills = st.text_area(
                "Skills to Learn", st.session_state.sg_skills, height=150,
                placeholder="e.g. Docker, MLOps, Apache Spark, Kubernetes, Airflow",
            )
            sg_skills_final = st.session_state.sg_skills
        else:
            sg_skills_final = ", ".join(ats_missing)
            st.info(f"Using {len(ats_missing)} missing skills from your ATS analysis.")
            st.markdown(" ".join([f"`{s}`" for s in ats_missing]))

    with col2:
        st.subheader("Roadmap Settings")
        st.session_state.sg_weeks = st.select_slider(
            "Duration", options=["2", "4", "6", "8", "12"],
            value=st.session_state.sg_weeks,
        )
        sg_level = st.selectbox(
            "Your Current Level",
            ["Complete Beginner", "Some Basics",
             "Intermediate", "Advanced in some areas"],
        )
        sg_time = st.selectbox(
            "Hours available per week",
            ["2-3 hrs", "4-6 hrs", "7-10 hrs", "10+ hrs"],
        )
        sg_style = st.selectbox(
            "Preferred Learning Style",
            ["Video courses + practice",
             "Documentation + projects",
             "Hands-on projects only",
             "Blend of all"],
        )

    st.divider()
    if st.button("📚 Generate My Roadmap", type="primary",
                 use_container_width=True):
        if not sg_skills_final.strip():
            st.error("Please enter the skills you want to learn.")
        else:
            with st.spinner("Building your personalised learning roadmap..."):
                data, err = gj(
                    system=(
                        "You are an expert technical learning coach. "
                        "Create specific, actionable roadmaps with ONLY free or "
                        "widely available resources. Output JSON only."
                    ),
                    user=(
                        f"Create a {st.session_state.sg_weeks}-week roadmap:\n"
                        f"Target Role: {st.session_state.sg_role or 'General tech'}\n"
                        f"Skills to learn: {sg_skills_final}\n"
                        f"Current level: {sg_level}\n"
                        f"Time available: {sg_time} per week\n"
                        f"Learning style: {sg_style}\n\n"
                        "Return JSON:\n"
                        "- summary: 2-sentence overview of the plan\n"
                        "- weeks: list of objects, each:\n"
                        "    - week_range: e.g. 'Week 1-2'\n"
                        "    - focus: main skill/topic for this period\n"
                        "    - goal: what you'll be able to do by the end\n"
                        "    - daily_tasks: list of 3-4 specific tasks\n"
                        "    - resources: list of 2-3 FREE resources "
                        "(name + type e.g. 'fast.ai — free course', "
                        "'official Kubernetes docs', 'YouTube: TechWorld with Nana')\n"
                        "    - project: one hands-on mini project for this period\n"
                        "- final_project: capstone that uses ALL the skills learned\n"
                        "- pro_tips: list of 3 learning tips specific to these skills\n\n"
                        'Schema: {"summary":"","weeks":[{"week_range":"","focus":"",'
                        '"goal":"","daily_tasks":[],"resources":[],"project":""}],'
                        '"final_project":"","pro_tips":[]}'
                    ),
                )
            if err or not data:
                st.error(f"Error: {err}")
            else:
                st.session_state.sg_result = data

    if st.session_state.sg_result:
        r = st.session_state.sg_result
        st.divider()
        st.subheader(
            f"📚 Your {st.session_state.sg_weeks}-Week Roadmap"
            + (f" — {st.session_state.sg_role}" if st.session_state.sg_role else "")
        )
        st.markdown(r.get("summary", ""))
        st.markdown("")

        weeks = r.get("weeks", [])
        WEEK_COLORS = ["#3b82f6","#8b5cf6","#ec4899",
                       "#f59e0b","#10b981","#06b6d4"]

        for i, w in enumerate(weeks):
            color = WEEK_COLORS[i % len(WEEK_COLORS)]
            with st.expander(
                f"📅 {w.get('week_range','')} — {w.get('focus','')}",
                expanded=(i == 0),
            ):
                st.markdown(f"**🎯 Goal:** {w.get('goal','')}")
                t_col, r_col = st.columns(2)
                with t_col:
                    st.markdown("**📋 Tasks**")
                    for t in w.get("daily_tasks", []):
                        st.markdown(f"- {t}")
                    if w.get("project"):
                        st.markdown(
                            f"**🛠️ Mini Project:** `{w['project']}`"
                        )
                with r_col:
                    st.markdown("**📖 Free Resources**")
                    for res in w.get("resources", []):
                        st.markdown(f"- {res}")

        st.divider()
        cap_col, tip_col = st.columns(2)
        with cap_col:
            st.markdown("**🏆 Capstone Project**")
            st.info(r.get("final_project", ""))
        with tip_col:
            st.markdown("**💡 Pro Tips**")
            for tip in r.get("pro_tips", []):
                st.markdown(f"- {tip}")

        st.divider()

        # PDF download
        if st.button("📥 Download Roadmap PDF", type="primary"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_margins(15, 15, 15)

            pdf.set_font("Helvetica", "B", 16)
            role_label = st.session_state.sg_role or "Tech Skills"
            pdf.cell(
                0, 11,
                latin(f"LEARNING ROADMAP — {role_label.upper()}"),
                align="C", ln=True,
            )
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(
                0, 6,
                latin(f"Duration: {st.session_state.sg_weeks} weeks  |  Skills: "
                      f"{sg_skills_final[:80]}"),
                align="C", ln=True,
            )
            pdf.ln(5)
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 5, latin(r.get("summary", "")))
            pdf.ln(4)

            for w in weeks:
                pdf.set_font("Helvetica", "B", 12)
                pdf.cell(
                    0, 8,
                    latin(f"{w.get('week_range','')} — {w.get('focus','')}"),
                    ln=True,
                )
                pdf.line(15, pdf.get_y(), 195, pdf.get_y())
                pdf.ln(2)
                pdf.set_font("Helvetica", "B", 10)
                pdf.multi_cell(0, 5, latin(f"Goal: {w.get('goal','')}"))
                pdf.set_font("Helvetica", "", 10)
                for t in w.get("daily_tasks", []):
                    pdf.multi_cell(0, 5, latin(f"  • {t}"))
                pdf.multi_cell(0, 5, "Resources:")
                for res in w.get("resources", []):
                    pdf.multi_cell(0, 5, latin(f"  → {res}"))
                if w.get("project"):
                    pdf.set_font("Helvetica", "I", 10)
                    pdf.multi_cell(0, 5, latin(f"Mini-project: {w['project']}"))
                pdf.ln(3)

            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "CAPSTONE PROJECT", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 5, latin(r.get("final_project", "")))
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "PRO TIPS", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for tip in r.get("pro_tips", []):
                pdf.multi_cell(0, 5, latin(f"• {tip}"))

            fname = role_label.replace(" ", "_")
            st.download_button(
                "⬇️ Save Roadmap PDF",
                data=pdf.output(),
                file_name=f"{fname}_Roadmap.pdf",
                mime="application/pdf",
            )

        if st.button("🔄 Build New Roadmap"):
            st.session_state.sg_result = None
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  INTERVIEW CHEAT SHEET
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.page == "cheatsheet":
    st.title("📝 Interview Cheat Sheet")
    st.caption("AI-generated 1-page prep brief for any company + role — read it 10 minutes before walking in.")
    st.divider()

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("The Interview")
        st.session_state.cs_role    = st.text_input(
            "Role *", st.session_state.cs_role,
            placeholder="e.g. Data Scientist",
        )
        st.session_state.cs_company = st.text_input(
            "Company *", st.session_state.cs_company,
            placeholder="e.g. Razorpay",
        )
        cs_round = st.selectbox(
            "Interview Round",
            ["Technical Round", "HR / Cultural Fit",
             "Managerial Round", "Final Round / Partner"],
        )
        cs_interviewer = st.text_input(
            "Interviewer Name (optional)",
            placeholder="e.g. Rahul Mehta — personalises the sheet",
        )
        st.session_state.cs_jd = st.text_area(
            "Job Description *", st.session_state.cs_jd, height=175,
            placeholder="Paste the full JD here...",
        )

    with col2:
        st.subheader("Your Background")
        has_resume = bool(st.session_state.r_blob)
        if has_resume:
            cs_src = st.radio(
                "Resume source",
                ["✅ Use Resume Builder output", "Paste manually"],
                index=0,
            )
        else:
            cs_src = st.radio("Resume source", ["Paste manually"], index=0)

        if "Paste manually" in cs_src:
            cs_resume = st.text_area(
                "Your resume / key highlights", height=200,
                placeholder="Paste resume text or key achievements...",
            )
        else:
            cs_resume = st.session_state.r_blob
            st.info(f"Using resume: **{st.session_state.r_name}**")

        cs_notes = st.text_area(
            "Anything specific to prepare for?", height=100,
            placeholder=(
                "e.g. They mentioned system design in the pre-screen call, "
                "I'm weaker on distributed systems..."
            ),
        )

    st.divider()
    if st.button("📝 Generate Cheat Sheet", type="primary",
                 use_container_width=True):
        if not st.session_state.cs_role or not st.session_state.cs_company:
            st.error("Role and company are required.")
        elif not st.session_state.cs_jd.strip():
            st.error("Please paste the job description.")
        else:
            with st.spinner("Building your cheat sheet..."):
                data, err = gj(
                    system=(
                        "You are a senior career coach who helps candidates "
                        "prepare for interviews at top companies. Be specific, "
                        "practical, and concise. Output JSON only."
                    ),
                    user=(
                        f"Create an interview cheat sheet for:\n"
                        f"Role: {st.session_state.cs_role}\n"
                        f"Company: {st.session_state.cs_company}\n"
                        f"Round: {cs_round}\n"
                        f"Interviewer: {cs_interviewer or 'Unknown'}\n"
                        f"JD: {st.session_state.cs_jd}\n"
                        f"Candidate background: {cs_resume or 'Not provided'}\n"
                        f"Special notes: {cs_notes or 'None'}\n\n"
                        "Return JSON:\n"
                        "- elevator_pitch: 3-4 sentence opening intro to use\n"
                        "- company_context: 2-3 sentences on what matters to this "
                        "company based on the JD (values, priorities, tech focus)\n"
                        "- key_points: list of 4-5 things to emphasize, tied to JD\n"
                        "- likely_questions: list of 6 likely questions for THIS "
                        "specific role/round, each with:\n"
                        "    - q: the question\n"
                        "    - bullet_answer: list of 3-4 bullet points to cover\n"
                        "- questions_to_ask: list of 3 smart questions to ask them\n"
                        "- red_flags_to_address: list of 2 likely weaknesses to "
                        "proactively address\n"
                        "- quick_reminders: list of 5 quick logistics/mindset tips\n\n"
                        'Schema: {"elevator_pitch":"","company_context":"",'
                        '"key_points":[],"likely_questions":[{"q":"","bullet_answer":[]}],'
                        '"questions_to_ask":[],"red_flags_to_address":[],'
                        '"quick_reminders":[]}'
                    ),
                )
            if err or not data:
                st.error(f"Error: {err}")
            else:
                st.session_state.cs_result = data

    if st.session_state.cs_result:
        r = st.session_state.cs_result
        st.divider()
        st.subheader(
            f"📝 {st.session_state.cs_role} at {st.session_state.cs_company}"
            f" — {cs_round}"
        )

        # Elevator pitch
        st.markdown("### 🎯 Your Opening Pitch")
        st.info(r.get("elevator_pitch", ""))
        st.markdown("")

        # Company context + key points
        cc, kp = st.columns(2)
        with cc:
            st.markdown("**🏢 Company Context (from JD)**")
            st.markdown(r.get("company_context", ""))
        with kp:
            st.markdown("**✅ Key Points to Emphasize**")
            for pt in r.get("key_points", []):
                st.markdown(f"- {pt}")

        st.divider()

        # Likely questions
        st.subheader("❓ Likely Questions & How to Answer")
        for i, lq in enumerate(r.get("likely_questions", [])):
            with st.expander(f"Q{i+1}: {lq.get('q','')}", expanded=(i < 2)):
                for b in lq.get("bullet_answer", []):
                    st.markdown(f"- {b}")

        st.divider()

        # Bottom row: questions + weaknesses + reminders
        qa_col, rf_col, rem_col = st.columns(3)
        with qa_col:
            st.markdown("**❓ Questions to Ask Them**")
            for q in r.get("questions_to_ask", []):
                st.markdown(f"- {q}")
        with rf_col:
            st.markdown("**⚠️ Weaknesses to Address**")
            for rf in r.get("red_flags_to_address", []):
                st.markdown(f"- 🔴 {rf}")
        with rem_col:
            st.markdown("**⚡ Quick Reminders**")
            for rem in r.get("quick_reminders", []):
                st.markdown(f"- {rem}")

        st.divider()

        # PDF download — compact 1-pager
        if st.button("📥 Download Cheat Sheet PDF", type="primary"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_margins(12, 12, 12)

            def cs_sec(title: str) -> None:
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 7, latin(title), ln=True)
                pdf.line(12, pdf.get_y(), 198, pdf.get_y())
                pdf.ln(2)

            # Header
            pdf.set_font("Helvetica", "B", 15)
            pdf.cell(
                0, 10,
                latin(f"INTERVIEW CHEAT SHEET — "
                      f"{st.session_state.cs_role.upper()}"),
                align="C", ln=True,
            )
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(
                0, 6,
                latin(f"{st.session_state.cs_company}  ·  {cs_round}"),
                align="C", ln=True,
            )
            pdf.ln(4)

            cs_sec("YOUR OPENING PITCH")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 5, latin(r.get("elevator_pitch", "")))
            pdf.ln(3)

            cs_sec("COMPANY CONTEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 5, latin(r.get("company_context", "")))
            pdf.ln(3)

            cs_sec("KEY POINTS TO EMPHASIZE")
            pdf.set_font("Helvetica", "", 10)
            for pt in r.get("key_points", []):
                pdf.multi_cell(0, 5, latin(f"✓  {pt}"))
            pdf.ln(3)

            cs_sec("LIKELY QUESTIONS")
            for i, lq in enumerate(r.get("likely_questions", [])):
                pdf.set_font("Helvetica", "B", 10)
                pdf.multi_cell(0, 5, latin(f"Q{i+1}: {lq.get('q','')}"))
                pdf.set_font("Helvetica", "", 9)
                for b in lq.get("bullet_answer", []):
                    pdf.multi_cell(0, 4, latin(f"   •  {b}"))
                pdf.ln(2)

            cs_sec("QUESTIONS TO ASK THEM")
            pdf.set_font("Helvetica", "", 10)
            for q in r.get("questions_to_ask", []):
                pdf.multi_cell(0, 5, latin(f"→  {q}"))
            pdf.ln(3)

            cs_sec("WEAKNESSES TO ADDRESS")
            pdf.set_font("Helvetica", "", 10)
            for rf in r.get("red_flags_to_address", []):
                pdf.multi_cell(0, 5, latin(f"!  {rf}"))
            pdf.ln(3)

            cs_sec("QUICK REMINDERS")
            pdf.set_font("Helvetica", "", 10)
            for rem in r.get("quick_reminders", []):
                pdf.multi_cell(0, 5, latin(f"⚡  {rem}"))

            fname = (
                f"{st.session_state.cs_company}_{st.session_state.cs_role}"
            ).replace(" ", "_")
            st.download_button(
                "⬇️ Save Cheat Sheet PDF",
                data=pdf.output(),
                file_name=f"{fname}_CheatSheet.pdf",
                mime="application/pdf",
            )

        if st.button("🔄 New Cheat Sheet"):
            st.session_state.cs_result = None
            st.rerun()
