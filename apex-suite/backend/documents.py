# ─────────────────────────────────────────────────────────────────────────────
#  APEX SUITE  ·  Document Generation
#  Real PDF/PPTX file builders, called from main.py's /api/documents/* routes.
#  Kept as a separate module so main.py doesn't balloon — pure functions here,
#  each takes plain data (already-validated by Pydantic in main.py) and
#  returns raw file bytes ready to stream back to the browser.
# ─────────────────────────────────────────────────────────────────────────────

import io
from fpdf import FPDF
from pptx import Presentation


# ── SHARED HELPERS ────────────────────────────────────────────────────────────

# Characters AI-generated text commonly uses that Latin-1 can't represent —
# transliterated to safe equivalents instead of falling through to Latin-1's
# crude "replace with ?" behavior, which would otherwise silently corrupt
# real Groq output (em-dashes and curly quotes show up constantly in it).
_UNICODE_FIXUPS = {
    "\u2014": "-",    # em dash  —
    "\u2013": "-",    # en dash  –
    "\u2018": "'",    # left single quote  '
    "\u2019": "'",    # right single quote  '
    "\u201c": '"',    # left double quote  "
    "\u201d": '"',    # right double quote  "
    "\u2026": "...",  # ellipsis  …
    "\u2022": "-",    # bullet  •
    "\u00b7": "|",    # middle dot  ·
}


def _safe(text: str) -> str:
    """FPDF's core fonts are Latin-1 only — this strips anything that would
    otherwise crash generation (smart quotes, emoji, etc.) instead of failing."""
    text = str(text)
    for uni, ascii_eq in _UNICODE_FIXUPS.items():
        text = text.replace(uni, ascii_eq)
    return text.encode("latin-1", "replace").decode("latin-1")


def _strip_tags(text: str) -> str:
    """The AI output wraps metrics in <b> and tools in <i> for on-screen
    display — plain PDF text doesn't render HTML, so these get stripped."""
    return (
        str(text)
        .replace("<b>", "").replace("</b>", "")
        .replace("<i>", "").replace("</i>", "")
    )


def _clean(text: str) -> str:
    return _safe(_strip_tags(text))


# ── RESUME PDF ────────────────────────────────────────────────────────────────

def build_resume_pdf(data: dict) -> bytes:
    """
    data = {
      name, email, phone, linkedin, github,
      edu, skills, exp: [str, ...], proj: [str, ...]
    }
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(18, 16, 18)

    # Header
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 12, _clean((data.get("name") or "").upper()), align="C", ln=True)

    pdf.set_font("Helvetica", "", 10)
    contact_parts = [p for p in [data.get("email"), data.get("phone")] if p]
    if data.get("linkedin"):
        contact_parts.append(data["linkedin"])
    if data.get("github"):
        contact_parts.append(data["github"])
    pdf.cell(0, 6, _clean(" | ".join(contact_parts)), align="C", ln=True)
    pdf.ln(6)

    def section(title: str) -> None:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, _clean(title), ln=True)
        pdf.set_draw_color(180, 170, 155)
        pdf.line(18, pdf.get_y(), 192, pdf.get_y())
        pdf.ln(3)

    if data.get("edu"):
        section("EDUCATION")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, _clean(data["edu"]))
        pdf.ln(4)

    if data.get("exp"):
        section("EXPERIENCE")
        pdf.set_font("Helvetica", "", 10)
        for bullet in data["exp"]:
            pdf.multi_cell(0, 5, f"-  {_clean(bullet)}")
            pdf.ln(1)
        pdf.ln(3)

    if data.get("proj"):
        section("PROJECTS")
        pdf.set_font("Helvetica", "", 10)
        for bullet in data["proj"]:
            pdf.multi_cell(0, 5, f"-  {_clean(bullet)}")
            pdf.ln(1)
        pdf.ln(3)

    if data.get("skills"):
        section("SKILLS")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, _clean(data["skills"]))

    return bytes(pdf.output())


# ── PORTFOLIO PPTX ────────────────────────────────────────────────────────────

def build_portfolio_pptx(data: dict) -> bytes:
    """
    data = { name, tagline, slides: [{title, content}, ...] }
    """
    prs = Presentation()

    title_slide = prs.slides.add_slide(prs.slide_layouts[0])
    title_slide.shapes.title.text = data.get("name", "")
    if len(title_slide.placeholders) > 1:
        title_slide.placeholders[1].text = data.get("tagline", "")

    for slide_data in data.get("slides", []):
        s = prs.slides.add_slide(prs.slide_layouts[1])
        s.shapes.title.text = slide_data.get("title", "")
        if len(s.placeholders) > 1:
            s.placeholders[1].text = slide_data.get("content", "")

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


# ── INTERVIEW CHEAT SHEET PDF ─────────────────────────────────────────────────

def build_cheatsheet_pdf(data: dict) -> bytes:
    """
    data = {
      role, company, round,
      elevator_pitch, company_context, key_points: [str],
      likely_questions: [{q, bullet_answer: [str]}],
      questions_to_ask: [str], red_flags_to_address: [str],
      quick_reminders: [str]
    }
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(14, 14, 14)

    def section(title: str) -> None:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, _clean(title), ln=True)
        pdf.set_draw_color(180, 170, 155)
        pdf.line(14, pdf.get_y(), 196, pdf.get_y())
        pdf.ln(2)

    # Header
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _clean(f"INTERVIEW CHEAT SHEET - {data.get('role', '').upper()}"),
             align="C", ln=True)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, _clean(f"{data.get('company', '')}  |  {data.get('round', '')}"),
              align="C", ln=True)
    pdf.ln(4)

    if data.get("elevator_pitch"):
        section("YOUR OPENING PITCH")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, _clean(data["elevator_pitch"]))
        pdf.ln(3)

    if data.get("company_context"):
        section("COMPANY CONTEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, _clean(data["company_context"]))
        pdf.ln(3)

    if data.get("key_points"):
        section("KEY POINTS TO EMPHASIZE")
        pdf.set_font("Helvetica", "", 10)
        for pt in data["key_points"]:
            pdf.multi_cell(0, 5, f"[+]  {_clean(pt)}")
            pdf.ln(1)
        pdf.ln(2)

    if data.get("likely_questions"):
        section("LIKELY QUESTIONS")
        for i, lq in enumerate(data["likely_questions"]):
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 5, _clean(f"Q{i+1}: {lq.get('q', '')}"))
            pdf.ln(1)
            pdf.set_font("Helvetica", "", 9)
            for b in lq.get("bullet_answer", []):
                pdf.multi_cell(0, 4, _clean(f"    -  {b}"))
                pdf.ln(1)
            pdf.ln(2)

    if data.get("questions_to_ask"):
        section("QUESTIONS TO ASK THEM")
        pdf.set_font("Helvetica", "", 10)
        for q in data["questions_to_ask"]:
            pdf.multi_cell(0, 5, f"->  {_clean(q)}")
            pdf.ln(1)
        pdf.ln(2)

    if data.get("red_flags_to_address"):
        section("WEAKNESSES TO ADDRESS")
        pdf.set_font("Helvetica", "", 10)
        for rf in data["red_flags_to_address"]:
            pdf.multi_cell(0, 5, f"!  {_clean(rf)}")
            pdf.ln(1)
        pdf.ln(2)

    if data.get("quick_reminders"):
        section("QUICK REMINDERS")
        pdf.set_font("Helvetica", "", 10)
        for r in data["quick_reminders"]:
            pdf.multi_cell(0, 5, f"*  {_clean(r)}")
            pdf.ln(1)

    return bytes(pdf.output())


# ── COVER LETTER PDF ──────────────────────────────────────────────────────────

def build_coverletter_pdf(data: dict) -> bytes:
    """
    data = { name, role, company, letter_text }
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _clean(data.get("name") or "Cover Letter"), ln=True)

    if data.get("role") or data.get("company"):
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, _clean(
            f"Application for {data.get('role','')} at {data.get('company','')}"
        ), ln=True)
    pdf.ln(6)

    pdf.set_font("Helvetica", "", 11)
    # Render each non-empty line as its own paragraph block. Every multi_cell
    # call is followed by ln() — the fix learned from the cheat sheet crash,
    # where multi_cell leaves the cursor near the right margin instead of
    # resetting it, corrupting the next call if nothing resets X first.
    paragraphs = [p.strip() for p in data.get("letter_text", "").split("\n") if p.strip()]
    for para in paragraphs:
        pdf.multi_cell(0, 6, _clean(para))
        pdf.ln(4)

    return bytes(pdf.output())


# ── MOCK INTERVIEW REPORT PDF ─────────────────────────────────────────────────

def build_interview_report_pdf(data: dict) -> bytes:
    """
    data = {
      role, overall_score, readiness_label, overall_feedback,
      top_strengths: [str], critical_gaps: [str],
      study_topics: [str], next_steps: [str],
      qa: [{question, category, answer, score, feedback}]
    }
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(16, 16, 16)

    def section(title: str) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _clean(title), ln=True)
        pdf.set_draw_color(180, 170, 155)
        pdf.line(16, pdf.get_y(), 194, pdf.get_y())
        pdf.ln(2)

    # Header
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 11, "MOCK INTERVIEW REPORT", align="C", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, _clean(f"Role: {data.get('role', '')}"), align="C", ln=True)
    pdf.ln(4)

    # Score summary
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, _clean(
        f"Overall Score: {data.get('overall_score', 0)}/100  -  {data.get('readiness_label', '')}"
    ), ln=True)
    pdf.ln(1)
    if data.get("overall_feedback"):
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, _clean(data["overall_feedback"]))
        pdf.ln(1)
    pdf.ln(3)

    if data.get("top_strengths"):
        section("TOP STRENGTHS")
        pdf.set_font("Helvetica", "", 10)
        for s in data["top_strengths"]:
            pdf.multi_cell(0, 5, f"+  {_clean(s)}")
            pdf.ln(1)
        pdf.ln(2)

    if data.get("critical_gaps"):
        section("CRITICAL GAPS")
        pdf.set_font("Helvetica", "", 10)
        for g in data["critical_gaps"]:
            pdf.multi_cell(0, 5, f"-  {_clean(g)}")
            pdf.ln(1)
        pdf.ln(2)

    if data.get("study_topics"):
        section("STUDY TOPICS")
        pdf.set_font("Helvetica", "", 10)
        for t in data["study_topics"]:
            pdf.multi_cell(0, 5, f"*  {_clean(t)}")
            pdf.ln(1)
        pdf.ln(2)

    if data.get("next_steps"):
        section("7-DAY ACTION PLAN")
        pdf.set_font("Helvetica", "", 10)
        for n in data["next_steps"]:
            pdf.multi_cell(0, 5, f"->  {_clean(n)}")
            pdf.ln(1)
        pdf.ln(3)

    if data.get("qa"):
        section("DETAILED Q&A REVIEW")
        for i, item in enumerate(data["qa"]):
            score = item.get("score", 0)
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 5, _clean(
                f"Q{i+1} [{item.get('category', '')}] - Score: {score}/10"
            ))
            pdf.ln(1)
            pdf.set_font("Helvetica", "I", 9)
            pdf.multi_cell(0, 5, _clean(item.get("question", "")))
            pdf.ln(1)
            pdf.set_font("Helvetica", "", 9)
            pdf.multi_cell(0, 5, _clean(f"Answer: {item.get('answer', '')}"))
            pdf.ln(1)
            if item.get("feedback"):
                pdf.multi_cell(0, 5, _clean(f"Feedback: {item.get('feedback', '')}"))
                pdf.ln(1)
            pdf.ln(2)

    return bytes(pdf.output())


# ── SKILL-GAP ROADMAP PDF ─────────────────────────────────────────────────────

def build_roadmap_pdf(data: dict) -> bytes:
    """
    data = {
      role, weeks_count, summary,
      weeks: [{week_range, focus, goal, daily_tasks: [str],
               resources: [str], project}],
      final_project, pro_tips: [str]
    }
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    def section(title: str) -> None:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, _clean(title), ln=True)
        pdf.set_draw_color(180, 170, 155)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(2)

    role_label = data.get("role") or "Tech Skills"
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 11, _clean(f"LEARNING ROADMAP - {role_label.upper()}"), align="C", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _clean(f"Duration: {data.get('weeks_count', '')} weeks"), align="C", ln=True)
    pdf.ln(4)

    if data.get("summary"):
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 5, _clean(data["summary"]))
        pdf.ln(1)
    pdf.ln(3)

    for w in data.get("weeks", []):
        pdf.set_font("Helvetica", "B", 12)
        pdf.multi_cell(0, 7, _clean(f"{w.get('week_range', '')} - {w.get('focus', '')}"))
        pdf.ln(1)
        pdf.set_draw_color(180, 170, 155)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(2)

        pdf.set_font("Helvetica", "B", 10)
        pdf.multi_cell(0, 5, _clean(f"Goal: {w.get('goal', '')}"))
        pdf.ln(1)

        pdf.set_font("Helvetica", "", 10)
        for t in w.get("daily_tasks", []):
            pdf.multi_cell(0, 5, _clean(f"  -  {t}"))
            pdf.ln(1)

        if w.get("resources"):
            pdf.set_font("Helvetica", "B", 9)
            pdf.multi_cell(0, 5, "Resources:")
            pdf.ln(1)
            pdf.set_font("Helvetica", "", 9)
            for r in w["resources"]:
                pdf.multi_cell(0, 5, _clean(f"  ->  {r}"))
                pdf.ln(1)

        if w.get("project"):
            pdf.set_font("Helvetica", "I", 9)
            pdf.multi_cell(0, 5, _clean(f"Mini-project: {w['project']}"))
            pdf.ln(1)
        pdf.ln(3)

    if data.get("final_project"):
        section("CAPSTONE PROJECT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, _clean(data["final_project"]))
        pdf.ln(1)
        pdf.ln(2)

    if data.get("pro_tips"):
        section("PRO TIPS")
        pdf.set_font("Helvetica", "", 10)
        for tip in data["pro_tips"]:
            pdf.multi_cell(0, 5, f"*  {_clean(tip)}")
            pdf.ln(1)

    return bytes(pdf.output())
