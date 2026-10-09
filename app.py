import streamlit as st
import os
import time
import json
from io import BytesIO
from dotenv import load_dotenv
from google import genai
from google.genai import types

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ GEMINI_API_KEY not found in .env file.")
    st.stop()

client = genai.Client(api_key=API_KEY)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📊",
    layout="wide",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
<style>

/* ---------- MAIN APP ---------- */

.stApp {
    background:
        radial-gradient(circle at 10% 10%, rgba(168,85,247,0.16), transparent 30%),
        radial-gradient(circle at 90% 15%, rgba(236,72,153,0.14), transparent 30%),
        radial-gradient(circle at 50% 90%, rgba(251,146,60,0.10), transparent 35%),
        #faf7ff;
}

.block-container {
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}


/* ---------- HERO ---------- */

.hero {
    text-align: center;
    padding: 30px 20px 40px 20px;
}

.hero h1 {
    font-size: 46px;
    font-weight: 800;
    background: linear-gradient(90deg, #7c3aed, #db2777, #ea580c);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 10px;
}

.hero p {
    font-size: 18px;
    color: #6b7280;
}


/* ---------- UPLOAD ---------- */

[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.82);
    border: 2px dashed #c084fc;
    border-radius: 18px;
    padding: 18px;
    transition: all 0.3s ease;
}

[data-testid="stFileUploader"]:hover {
    border-color: #a855f7;
    background: #fdf4ff;
    transform: translateY(-2px);
}


/* ---------- TEXT AREA ---------- */

.stTextArea textarea {
    border: 2px solid #eadcff !important;
    border-radius: 16px !important;
    background: rgba(255,255,255,0.88) !important;
    transition: all 0.3s ease !important;
}

.stTextArea textarea:focus {
    border-color: #a855f7 !important;
    box-shadow: 0 0 0 3px rgba(168,85,247,0.12) !important;
}


/* ---------- BUTTON ---------- */

.stButton > button {
    width: 100%;
    border: none;
    border-radius: 14px;
    padding: 14px 25px;
    font-size: 17px;
    font-weight: 700;
    color: white;
    background: linear-gradient(90deg, #7c3aed, #db2777, #ea580c);
    box-shadow: 0 8px 20px rgba(124,58,237,0.25);
    transition: all 0.25s ease;
}

.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 30px rgba(219,39,119,0.30);
    filter: brightness(1.06);
}

.stButton > button:active {
    transform: translateY(0);
}


/* ---------- METRICS ---------- */

[data-testid="stMetric"] {
    background: rgba(255,255,255,0.88);
    border: 1px solid #eadcff;
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 6px 20px rgba(88,28,135,0.07);
    transition: all 0.25s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 28px rgba(168,85,247,0.15);
}


/* ---------- PROGRESS ---------- */

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #7c3aed, #db2777, #f97316);
}


/* ---------- ALERTS ---------- */

[data-testid="stAlert"] {
    border-radius: 14px;
    border: none;
    box-shadow: 0 5px 18px rgba(88,28,135,0.06);
}


/* ---------- HEADINGS ---------- */

h2, h3 {
    color: #2e1065;
    font-weight: 750;
}


/* ---------- DIVIDER ---------- */

hr {
    border: none;
    height: 1px;
    background: linear-gradient(
        90deg,
        transparent,
        #d8b4fe,
        #f9a8d4,
        transparent
    );
    margin: 30px 0;
}


/* ---------- MOBILE ---------- */

@media (max-width: 768px) {
    .hero h1 {
        font-size: 34px;
    }

    .hero p {
        font-size: 15px;
    }

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
<div class="hero">
    <h1>📊 AI Resume Analyzer</h1>
    <p>Analyze your resume against any job description using Generative AI</p>
</div>
""",
    unsafe_allow_html=True,
)


# =========================================================
# INPUT SECTION
# =========================================================

left, right = st.columns(2)

with left:
    st.subheader("📄 Upload Resume")
    st.caption("Upload your resume in PDF format.")

    uploaded_file = st.file_uploader(
        "Choose your resume",
        type=["pdf"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.success(f"Resume uploaded: {uploaded_file.name}")


with right:
    st.subheader("💼 Job Description")
    st.caption("Paste the job description you want to apply for.")

    job_description = st.text_area(
        "Job Description",
        height=260,
        placeholder="""Example:

We are looking for an AI/ML Intern.

Requirements:
- Python
- Machine Learning
- Pandas
- NumPy
- SQL
- NLP
- Generative AI
- Problem solving
- Good communication skills

Responsibilities:
- Build machine learning models
- Analyze datasets
- Work with AI APIs
- Develop AI-based applications
- Perform data preprocessing
""",
        label_visibility="collapsed",
    )


# =========================================================
# ANALYSIS FUNCTION
# =========================================================

def analyze_resume(pdf_bytes, job_description):
    """
    Send the resume PDF and job description to Gemini.

    Returns:
        tuple[str, str]: raw JSON response text and model name.
    """

    # Keep the working model first.
    # Other models are fallback options if the first one is busy.
    models = [
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.6-flash",
        "gemini-3.7-flash",
        "gemini-3.8-flash",
    ]

    prompt = f"""
You are an expert ATS Resume Analyzer, technical recruiter,
and career advisor.

Your job is to analyze the uploaded resume PDF against the
provided job description.

IMPORTANT RULES:

1. Carefully read the uploaded PDF.
2. The PDF may be text-based or scanned/image-based.
3. Read visible text from the PDF even if normal text extraction
   would fail.
4. Do NOT assume the resume is empty.
5. Do NOT invent skills, education, experience, projects,
   certifications, or achievements.
6. Only consider something a resume skill if it is actually
   present or clearly demonstrated in the resume.
7. Compare the resume with the job description.
8. Calculate a realistic ATS-style match score from 0 to 100.
9. Consider:
   - Required skills
   - Technical skills
   - Responsibilities
   - Education
   - Projects
   - Experience
   - Relevant keywords
10. Do not give a high score simply because the candidate is
    capable of learning something.
11. Missing skills must actually be missing from the resume.
12. Matching skills must actually appear in or be demonstrated
    by the resume.
13. Recommendations should be practical and specific.
14. Never fabricate candidate information.
15. Extract the most important ATS keywords from the job description.
16. Check which important keywords are actually present or clearly
    demonstrated in the resume.
17. Do not count generic or unrelated words as ATS keywords.
18. keyword_match_score must be an integer from 0 to 100.
19. ats_keywords_found must contain only keywords supported by the resume.
20. ats_keywords_missing must contain important job-description
    keywords that are not supported by the resume.
21. Do not mark a keyword as found merely because it is a similar
    or unrelated word.
22. Keep the ATS keyword lists focused on meaningful skills,
    tools, technologies, methods, qualifications, and role-specific
    terms.
23. strengths must be based only on actual resume content.
24. weaknesses must be realistic and supported by the comparison.
25. professional_summary must be 3-5 useful sentences.
26. improved_professional_summary must be a rewritten, job-targeted summary based ONLY on facts actually present in the resume. Do not invent experience or skills.
27. skills_to_add must contain relevant skills from the job description that are missing from the resume.
28. sections_to_improve must identify resume sections that need improvement and explain what to improve.
29. project_suggestions must be realistic project ideas relevant to the target role. These are suggestions only and must never be presented as completed projects.
30. ats_improvement_tips must be practical, specific tips for improving ATS compatibility without keyword stuffing or false claims.
31. Extract candidate_name from the resume exactly as written when available.
32. Extract degree_course from the resume, such as B.Tech in Computer Science, B.E., MBA, Diploma, etc.
33. Extract college_university from the resume when available.
34. Extract experience_level from the resume, such as Fresher, Student, Internship, or Experienced. Do not invent experience.
35. Extract target_role from the job description as the role the candidate is being evaluated for.
36. If any candidate detail is not available, return "Not specified" instead of guessing.

JOB DESCRIPTION:

{job_description}

RETURN ONLY VALID JSON.

Use exactly this structure:

{{
    "match_score": 0,
    "keyword_match_score": 0,
    "matching_skills": [],
    "missing_skills": [],
    "ats_keywords_found": [],
    "ats_keywords_missing": [],
    "strengths": [],
    "weaknesses": [],
    "recommendations": [],
    "professional_summary": "",
    "improved_professional_summary": "",
    "skills_to_add": [],
    "sections_to_improve": [],
    "project_suggestions": [],
    "ats_improvement_tips": [],
    "candidate_name": "Not specified",
    "degree_course": "Not specified",
    "college_university": "Not specified",
    "experience_level": "Not specified",
    "target_role": "Not specified"
}}

Additional rules:

- match_score must be an integer from 0 to 100.
- keyword_match_score must be an integer from 0 to 100.
- matching_skills must contain only skills supported by the resume.
- missing_skills must contain important job requirements that are
  not supported by the resume.
- ats_keywords_found must contain only meaningful keywords actually
  present or clearly demonstrated in the resume.
- ats_keywords_missing must contain important keywords from the
  job description that are not supported by the resume.
- strengths must be based on actual resume content.
- weaknesses must be realistic.
- recommendations must be actionable.
- professional_summary should be 3-5 sentences.
- improved_professional_summary should be 3-5 sentences and use only facts from the resume.
- skills_to_add should contain relevant missing skills, not fabricated current skills.
- sections_to_improve should be concise and actionable.
- project_suggestions should clearly be suggestions, not claims about the candidate.
- ats_improvement_tips should be specific and practical.
- candidate_name, degree_course, college_university, experience_level, and target_role must be based only on the resume/job description as specified above.
- Use "Not specified" when the information is unavailable.
"""

    pdf_part = types.Part.from_bytes(
        data=pdf_bytes,
        mime_type="application/pdf",
    )

    last_error = None

    # =====================================================
    # MODEL RETRY / FALLBACK SYSTEM
    # =====================================================

    for model_name in models:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        pdf_part,
                        prompt,
                    ],
                )

                if response and response.text:
                    return response.text, model_name

                last_error = Exception("Gemini returned an empty response.")

            except Exception as e:
                last_error = e
                error_text = str(e).upper()

                # Temporary overload.
                if "503" in error_text or "UNAVAILABLE" in error_text:
                    time.sleep(2 ** attempt)
                    continue

                # Rate limit / quota.
                if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                    time.sleep(3 ** attempt)
                    continue

                # Authentication, invalid request, etc.
                break

    raise Exception(
        f"Gemini analysis failed. Last error: {last_error}"
    )


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def safe_int(value, default=0):
    """Convert a value to an integer and keep it between 0 and 100."""
    try:
        value = int(float(value))
    except (TypeError, ValueError):
        value = default

    return max(0, min(100, value))


def clean_list(value):
    """Return a clean list of strings from an AI response field."""
    if not isinstance(value, list):
        return []

    cleaned = []

    for item in value:
        if item is None:
            continue

        item = str(item).strip()

        if item and item not in cleaned:
            cleaned.append(item)

    return cleaned


def parse_ai_json(result_text):
    """
    Parse Gemini's JSON response.
    Handles normal JSON and markdown ```json ... ``` responses.
    """

    cleaned = result_text.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        # Remove opening and closing markdown fences.
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    # First attempt: normal JSON.
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Second attempt: find the outermost JSON object.
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1 and end > start:
        return json.loads(cleaned[start:end + 1])

    raise ValueError("Gemini did not return valid JSON.")


# =========================================================
# PDF REPORT GENERATOR - STEP 4
# =========================================================

def build_pdf_report(result_text, resume_name, job_description, model_name):
    """Create a professional PDF report from the Gemini JSON analysis."""

    data = parse_ai_json(result_text)

    score = safe_int(data.get("match_score", 0))
    keyword_score = safe_int(data.get("keyword_match_score", 0))

    matching = clean_list(data.get("matching_skills", []))
    missing = clean_list(data.get("missing_skills", []))
    keywords_found = clean_list(data.get("ats_keywords_found", []))
    keywords_missing = clean_list(data.get("ats_keywords_missing", []))
    strengths = clean_list(data.get("strengths", []))
    weaknesses = clean_list(data.get("weaknesses", []))
    recommendations = clean_list(data.get("recommendations", []))
    skills_to_add = clean_list(data.get("skills_to_add", []))
    sections_to_improve = clean_list(data.get("sections_to_improve", []))
    project_suggestions = clean_list(data.get("project_suggestions", []))
    ats_tips = clean_list(data.get("ats_improvement_tips", []))

    candidate_name = str(data.get("candidate_name", "Not specified")).strip() or "Not specified"
    degree_course = str(data.get("degree_course", "Not specified")).strip() or "Not specified"
    college_university = str(data.get("college_university", "Not specified")).strip() or "Not specified"
    experience = str(data.get("experience", "Not specified")).strip() or "Not specified"
    target_role = str(data.get("target_role", "Not specified")).strip() or "Not specified"

    summary = str(data.get("professional_summary", "")).strip()
    improved_summary = str(data.get("improved_professional_summary", "")).strip()

    candidate_name = str(data.get("candidate_name", "Not specified")).strip() or "Not specified"
    degree_course = str(data.get("degree_course", "Not specified")).strip() or "Not specified"
    college_university = str(data.get("college_university", "Not specified")).strip() or "Not specified"
    experience_level = str(data.get("experience_level", "Not specified")).strip() or "Not specified"
    target_role = str(data.get("target_role", "Not specified")).strip() or "Not specified"

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="AI Resume Analysis Report",
        author="AI Resume Analyzer",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=23,
        leading=28,
        textColor=colors.HexColor("#6d28d9"),
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.HexColor("#6b7280"),
        spaceAfter=18,
    )
    heading_style = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#4c1d95"),
        spaceBefore=12,
        spaceAfter=7,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#374151"),
        spaceAfter=5,
    )
    small_style = ParagraphStyle(
        "ReportSmall",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#6b7280"),
    )

    def safe_text(value):
        return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def bullet_list(items):
        flow = []
        if not items:
            flow.append(Paragraph("None identified.", body_style))
            return flow
        for item in items:
            flow.append(Paragraph(f"• {safe_text(item)}", body_style))
        return flow

    story = []

    story.append(Paragraph("Resume Analysis Report", title_style))
    story.append(Paragraph(
        "ATS-focused resume analysis and job-match report",
        subtitle_style,
    ))

    meta_data = [
        [Paragraph("Candidate Name", body_style), Paragraph(safe_text(candidate_name), body_style)],
        [Paragraph("Degree / Course", body_style), Paragraph(safe_text(degree_course), body_style)],
        [Paragraph("College / University", body_style), Paragraph(safe_text(college_university), body_style)],
        [Paragraph("Experience", body_style), Paragraph(safe_text(experience_level), body_style)],
        [Paragraph("Target Role", body_style), Paragraph(safe_text(target_role), body_style)],
    ]
    meta_table = Table(meta_data, colWidths=[35 * mm, 135 * mm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3e8ff")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#ddd6fe")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    score_data = [
        [
            Paragraph("Overall ATS Score", body_style),
            Paragraph("Keyword Match", body_style),
            Paragraph("Matching Skills", body_style),
            Paragraph("Missing Skills", body_style),
        ],
        [
            Paragraph(f"<b>{score}%</b>", body_style),
            Paragraph(f"<b>{keyword_score}%</b>", body_style),
            Paragraph(f"<b>{len(matching)}</b>", body_style),
            Paragraph(f"<b>{len(missing)}</b>", body_style),
        ],
    ]
    score_table = Table(score_data, colWidths=[42 * mm] * 4)
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#faf5ff")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#d8b4fe")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(score_table)

    story.append(Paragraph("ATS Keyword Analysis", heading_style))
    story.extend(bullet_list([f"Keywords found: {len(keywords_found)}"] + keywords_found))
    story.extend(bullet_list([f"Keywords missing: {len(keywords_missing)}"] + keywords_missing))

    story.append(Paragraph("Matching Skills", heading_style))
    story.extend(bullet_list(matching))

    story.append(Paragraph("Missing Skills", heading_style))
    story.extend(bullet_list(missing))

    story.append(Paragraph("Strengths", heading_style))
    story.extend(bullet_list(strengths))

    story.append(Paragraph("Weaknesses", heading_style))
    story.extend(bullet_list(weaknesses))

    story.append(Paragraph("Recommendations", heading_style))
    story.extend(bullet_list(recommendations))

    story.append(PageBreak())

    story.append(Paragraph("AI Resume Improvement", heading_style))

    story.append(Paragraph("Suggested Professional Summary", heading_style))
    story.append(Paragraph(safe_text(improved_summary or "No improved summary generated."), body_style))

    story.append(Paragraph("Skills to Add or Strengthen", heading_style))
    story.extend(bullet_list(skills_to_add))

    story.append(Paragraph("Resume Sections to Improve", heading_style))
    story.extend(bullet_list(sections_to_improve))

    story.append(Paragraph("Recommended Projects", heading_style))
    story.extend(bullet_list(project_suggestions))

    story.append(Paragraph("ATS Improvement Tips", heading_style))
    story.extend(bullet_list(ats_tips))

    story.append(Paragraph("Current Professional Summary", heading_style))
    story.append(Paragraph(safe_text(summary or "No summary generated."), body_style))

    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Note: AI recommendations are suggestions. Do not add skills, projects, or experience to your resume unless they are truthful and you can support them.",
        small_style,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# =========================================================
# DISPLAY RESULT
# =========================================================

def display_analysis(result_text, resume_name="", job_description="", model_name=""):
    """Render the complete ATS dashboard."""

    # =====================================================
    # PARSE AI RESPONSE
    # =====================================================

    try:
        data = parse_ai_json(result_text)

    except Exception:
        st.warning(
            "⚠️ AI returned an unexpected format. Showing the raw response."
        )
        st.code(result_text, language="json")
        return

    if not isinstance(data, dict):
        st.error("❌ AI response is not a valid analysis object.")
        return

    candidate_name = str(data.get("candidate_name", "Not specified")).strip() or "Not specified"
    degree_course = str(data.get("degree_course", "Not specified")).strip() or "Not specified"
    college_university = str(data.get("college_university", "Not specified")).strip() or "Not specified"
    experience = str(data.get("experience", "Not specified")).strip() or "Not specified"
    target_role = str(data.get("target_role", "Not specified")).strip() or "Not specified"

    # =====================================================
    # GET AND NORMALIZE ALL DATA FIRST
    # =====================================================
    # IMPORTANT:
    # Every variable used below is created BEFORE the UI
    # sections use it. This prevents errors such as:
    # "cannot access local variable 'keyword_score'..."
    # =====================================================

    score = safe_int(data.get("match_score", 0))

    keyword_score = safe_int(
        data.get("keyword_match_score", 0)
    )

    matching = clean_list(
        data.get("matching_skills", [])
    )

    missing = clean_list(
        data.get("missing_skills", [])
    )

    keywords_found = clean_list(
        data.get("ats_keywords_found", [])
    )

    keywords_missing = clean_list(
        data.get("ats_keywords_missing", [])
    )

    strengths = clean_list(
        data.get("strengths", [])
    )

    weaknesses = clean_list(
        data.get("weaknesses", [])
    )

    recommendations = clean_list(
        data.get("recommendations", [])
    )

    summary = str(
        data.get(
            "professional_summary",
            "No professional summary generated.",
        )
    ).strip()

    if not summary:
        summary = "No professional summary generated."

    improved_summary = str(
        data.get(
            "improved_professional_summary",
            "No improved professional summary generated.",
        )
    ).strip()

    if not improved_summary:
        improved_summary = "No improved professional summary generated."

    skills_to_add = clean_list(
        data.get("skills_to_add", [])
    )

    sections_to_improve = clean_list(
        data.get("sections_to_improve", [])
    )

    project_suggestions = clean_list(
        data.get("project_suggestions", [])
    )

    ats_improvement_tips = clean_list(
        data.get("ats_improvement_tips", [])
    )

    # =====================================================
    # RESULT HEADER
    # =====================================================

    st.markdown("---")

    st.markdown("## 📊 Resume Analysis Dashboard")

    st.caption(
        "Personalized ATS analysis of your resume"
    )

    # =====================================================
    # CANDIDATE DETAILS
    # =====================================================

    st.markdown("### 👤 Candidate Details")
    detail1, detail2, detail3 = st.columns(3)
    with detail1:
        st.write(f"**Name:** {candidate_name}")
        st.write(f"**Degree / Course:** {degree_course}")
    with detail2:
        st.write(f"**College / University:** {college_university}")
        st.write(f"**Experience:** {experience}")
    with detail3:
        st.write(f"**Target Role:** {target_role}")

    # =====================================================
    # OVERALL SCORE
    # =====================================================

    if score >= 80:
        status = "🟢 Excellent Match"
    elif score >= 60:
        status = "🟡 Good Match"
    elif score >= 40:
        status = "🟠 Moderate Match"
    else:
        status = "🔴 Low Match"

    score_col, overview_col = st.columns([1, 2])

    with score_col:
        st.metric(
            "Overall ATS Score",
            f"{score}%",
        )

        st.write(status)

        st.progress(score / 100)

    with overview_col:
        st.markdown("### 🎯 ATS Match Overview")

        st.write(
            f"**{score}%** of the job requirements "
            "are aligned with your resume."
        )

        stat1, stat2, stat3 = st.columns(3)

        with stat1:
            st.metric(
                "✅ Matching",
                len(matching),
            )

        with stat2:
            st.metric(
                "❌ Missing",
                len(missing),
            )

        with stat3:
            st.metric(
                "🚀 Recommendations",
                len(recommendations),
            )

    # =====================================================
    # ATS KEYWORD ANALYSIS
    # =====================================================

    st.markdown("---")

    st.markdown("## 🔑 ATS Keyword Analysis")

    st.caption(
        "Important keywords from the job description compared with your resume."
    )

    keyword_col1, keyword_col2 = st.columns([1, 2])

    with keyword_col1:
        st.metric(
            "Keyword Match",
            f"{keyword_score}%",
        )

        st.progress(keyword_score / 100)

    with keyword_col2:
        if keyword_score >= 80:
            st.success(
                "🟢 Excellent keyword alignment"
            )
        elif keyword_score >= 60:
            st.info(
                "🟡 Good keyword alignment"
            )
        elif keyword_score >= 40:
            st.warning(
                "🟠 Moderate keyword alignment"
            )
        else:
            st.error(
                "🔴 Low keyword alignment"
            )

        st.write(
            f"Found **{len(keywords_found)}** important keywords "
            f"and missing **{len(keywords_missing)}**."
        )

    # =====================================================
    # FOUND ATS KEYWORDS
    # =====================================================

    st.markdown("### ✅ Keywords Found in Resume")

    if keywords_found:
        found_cols = st.columns(3)

        for i, keyword in enumerate(keywords_found):
            with found_cols[i % 3]:
                st.success(f"✓ {keyword}")
    else:
        st.info(
            "No important ATS keywords were identified."
        )

    # =====================================================
    # MISSING ATS KEYWORDS
    # =====================================================

    st.markdown("### ❌ Missing ATS Keywords")

    if keywords_missing:
        missing_cols = st.columns(3)

        for i, keyword in enumerate(keywords_missing):
            with missing_cols[i % 3]:
                st.warning(f"⚠ {keyword}")
    else:
        st.success(
            "🎉 No major ATS keywords are missing!"
        )

    # =====================================================
    # MATCHING SKILLS
    # =====================================================

    st.markdown("---")

    st.markdown("### ✅ Matching Skills")

    if matching:
        cols = st.columns(3)

        for i, skill in enumerate(matching):
            with cols[i % 3]:
                st.success(f"✓ {skill}")
    else:
        st.info(
            "No matching skills identified."
        )

    # =====================================================
    # MISSING SKILLS
    # =====================================================

    st.markdown("### ❌ Missing Skills")

    if missing:
        cols = st.columns(3)

        for i, skill in enumerate(missing):
            with cols[i % 3]:
                st.warning(f"⚠ {skill}")
    else:
        st.success(
            "🎉 No major missing skills identified!"
        )

    # =====================================================
    # STRENGTHS AND WEAKNESSES
    # =====================================================

    st.markdown("---")

    strength_col, weakness_col = st.columns(2)

    with strength_col:
        st.markdown("### 💪 Strengths")

        if strengths:
            for item in strengths:
                st.success(item)
        else:
            st.write(
                "No specific strengths identified."
            )

    with weakness_col:
        st.markdown("### ⚠️ Weaknesses")

        if weaknesses:
            for item in weaknesses:
                st.warning(item)
        else:
            st.write(
                "No major weaknesses identified."
            )

    # =====================================================
    # RECOMMENDATIONS
    # =====================================================

    st.markdown("---")

    st.markdown("### 🚀 How to Improve Your Resume")

    if recommendations:
        for i, recommendation in enumerate(
            recommendations,
            1,
        ):
            st.markdown(
                f"**{i}.** {recommendation}"
            )
    else:
        st.info(
            "No additional recommendations."
        )

    # =====================================================
    # PROFESSIONAL SUMMARY
    # =====================================================

    st.markdown("---")

    st.markdown("### 📝 Professional Summary")

    st.info(summary)

    # =====================================================
    # STEP 3 - AI RESUME IMPROVEMENT
    # =====================================================

    st.markdown("---")

    st.markdown("## 🚀 AI Resume Improvement")

    st.caption(
        "Actionable suggestions to make your resume stronger for this specific job."
    )

    # -----------------------------------------------------
    # IMPROVED PROFESSIONAL SUMMARY
    # -----------------------------------------------------

    st.markdown("### ✨ Suggested Professional Summary")

    st.info(improved_summary)

    st.caption(
        "This is an AI rewrite based only on information found in your resume. Review it before using it."
    )

    # -----------------------------------------------------
    # SKILLS TO ADD
    # -----------------------------------------------------

    st.markdown("### 🎯 Skills to Add or Strengthen")

    if skills_to_add:
        skill_cols = st.columns(3)

        for i, skill in enumerate(skills_to_add):
            with skill_cols[i % 3]:
                st.warning(f"➕ {skill}")
    else:
        st.success(
            "🎉 No additional job-specific skills were identified as necessary."
        )

    # -----------------------------------------------------
    # SECTIONS TO IMPROVE
    # -----------------------------------------------------

    st.markdown("### 📌 Resume Sections to Improve")

    if sections_to_improve:
        for i, item in enumerate(sections_to_improve, 1):
            st.markdown(f"**{i}.** {item}")
    else:
        st.success("Your major resume sections look relevant for this role.")

    # -----------------------------------------------------
    # PROJECT SUGGESTIONS
    # -----------------------------------------------------

    st.markdown("### 💼 Recommended Projects")

    if project_suggestions:
        project_cols = st.columns(2)

        for i, project in enumerate(project_suggestions):
            with project_cols[i % 2]:
                st.info(f"💡 {project}")
    else:
        st.info("No specific project suggestions were generated.")

    st.caption(
        "Project ideas are suggestions only. Add a project to your resume only after actually completing it."
    )

    # -----------------------------------------------------
    # ATS IMPROVEMENT TIPS
    # -----------------------------------------------------

    st.markdown("### 📈 ATS Improvement Tips")

    if ats_improvement_tips:
        for i, tip in enumerate(ats_improvement_tips, 1):
            st.markdown(f"**{i}.** {tip}")
    else:
        st.info("No additional ATS improvement tips were generated.")

    # =====================================================
    # STEP 4 - DOWNLOAD PDF REPORT
    # =====================================================

    st.markdown("---")

    st.markdown("## 📥 Download Analysis Report")

    st.caption(
        "Download the complete ATS analysis, keyword report, and AI improvement plan as a PDF."
    )

    try:
        pdf_report = build_pdf_report(
            result_text=result_text,
            resume_name=resume_name,
            job_description=job_description,
            model_name=model_name,
        )

        st.download_button(
            label="📄 Download Complete PDF Report",
            data=pdf_report,
            file_name="AI_Resume_Analysis_Report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

    except Exception as report_error:
        st.error(f"Could not generate PDF report: {report_error}")

    # =====================================================
    # FINAL TIP
    # =====================================================

    st.markdown("---")

    st.info(
        "💡 Use the missing skills, missing keywords, and "
        "recommendations to customize your resume for this specific job."
    )


# =========================================================
# SESSION STATE
# =========================================================

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "analysis_model" not in st.session_state:
    st.session_state.analysis_model = ""

if "analysis_resume_name" not in st.session_state:
    st.session_state.analysis_resume_name = ""

if "analysis_job_description" not in st.session_state:
    st.session_state.analysis_job_description = ""


# =========================================================
# ANALYZE BUTTON
# =========================================================

st.markdown("")

analyze_button = st.button(
    "🚀 Analyze Resume",
    type="primary",
    use_container_width=True,
)


if analyze_button:

    if not uploaded_file:
        st.error("❌ Please upload your resume PDF first.")

    elif not job_description.strip():
        st.error("❌ Please enter the job description first.")

    else:
        with st.spinner(
            "🤖 AI is reading your resume and comparing it with the job description..."
        ):
            try:
                pdf_bytes = uploaded_file.getvalue()

                result, used_model = analyze_resume(
                    pdf_bytes,
                    job_description,
                )

                st.session_state.analysis_result = result
                st.session_state.analysis_model = used_model
                st.session_state.analysis_resume_name = uploaded_file.name
                st.session_state.analysis_job_description = job_description

                st.success(
                    "✅ Analysis completed successfully"
                )

            except Exception as e:
                st.error(f"❌ Analysis failed: {e}")
                st.info("Please try again after a few seconds.")


# =========================================================
# DISPLAY SAVED ANALYSIS
# =========================================================

if st.session_state.analysis_result:

    display_analysis(
        st.session_state.analysis_result,
        resume_name=st.session_state.analysis_resume_name,
        job_description=st.session_state.analysis_job_description,
        model_name=st.session_state.analysis_model,
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.markdown(
    """
<div style="text-align:center; color:#777;">
    <p>Built with Python • Streamlit • Google Gemini</p>
    <p>AI Resume Analyzer — ATS-powered career assistant</p>
</div>
""",
    unsafe_allow_html=True,
)
