import streamlit as st
import asyncio
import sys
import os
from dotenv import load_dotenv

# ── Load API keys ─────────────────────────────────────────────────────────────
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
if hasattr(st, "secrets"):
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    if "GITHUB_TOKEN" in st.secrets:
        os.environ["GITHUB_TOKEN"] = st.secrets["GITHUB_TOKEN"]

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agents.profile_analyzer import profile_analyzer
from agents.career_planner import career_planner
from agents.resume_agent import resume_agent
from agents.project_generator import project_generator
from agents.interview_agent import interview_agent
from agents.learning_agent import learning_agent
from tools.security import mask_personal_data
import PyPDF2
import io

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CareerPilot AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

* { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #F7F8FA; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 2rem 2rem 2rem !important; max-width: 1200px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: #0F1117 !important; border-right: 1px solid #1E2130; }
.sidebar-logo { font-family:'Space Grotesk',sans-serif; font-size:1.4rem; font-weight:700; color:#FFFFFF; padding:1.5rem 0 0.5rem 0; }
.sidebar-tagline { font-size:0.75rem; color:#64748B; margin-bottom:2rem; }
.sidebar-section { font-size:0.65rem; font-weight:600; letter-spacing:1.5px; text-transform:uppercase; color:#475569; margin:1.5rem 0 0.75rem 0; }
.agent-item { display:flex; align-items:center; gap:10px; padding:8px 12px; border-radius:8px; margin-bottom:4px; font-size:0.85rem; color:#CBD5E1; }
.agent-item:hover { background:#1E2130; }
.agent-dot { width:6px; height:6px; border-radius:50%; background:#3B82F6; flex-shrink:0; }
.security-item { display:flex; align-items:center; gap:8px; font-size:0.8rem; color:#94A3B8; padding:4px 0; }

/* ── Cards ── */
.card { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; padding:1.5rem; margin-bottom:1.25rem; box-shadow:0 1px 3px rgba(0,0,0,0.04); }
.card-header { display:flex; align-items:center; gap:10px; margin-bottom:1.25rem; }
.card-icon { width:36px; height:36px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:1rem; flex-shrink:0; }
.icon-blue { background:#EFF6FF; } .icon-purple { background:#F5F3FF; }
.icon-green { background:#F0FDF4; } .icon-orange { background:#FFF7ED; }
.card-title { font-family:'Space Grotesk',sans-serif; font-size:0.95rem; font-weight:600; color:#0F172A; }
.card-desc { font-size:0.8rem; color:#64748B; margin-top:1px; }

/* ── Buttons ── */
.stButton > button[kind="primary"] {
    background:#0F172A !important; color:#FFFFFF !important; border:none !important;
    border-radius:10px !important; padding:0.65rem 1.5rem !important;
    font-size:0.875rem !important; font-weight:600 !important;
    transition:all 0.15s !important; box-shadow:0 1px 2px rgba(0,0,0,0.1) !important;
}
.stButton > button[kind="primary"]:hover { background:#1E293B !important; transform:translateY(-1px) !important; }
.stButton > button[kind="primary"]:disabled { background:#94A3B8 !important; cursor:not-allowed !important; transform:none !important; }
.stButton > button { border-radius:10px !important; font-weight:500 !important; }

/* ── Form Fields ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    border-radius:10px !important; border:1px solid #E2E8F0 !important;
    font-size:0.875rem !important; color:#0F172A !important; background:#FFFFFF !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color:#3B82F6 !important; box-shadow:0 0 0 3px rgba(59,130,246,0.1) !important;
}

/* ── Force dark text everywhere (fixes sidebar bleed) ── */
label, .stCheckbox label, .stCheckbox p, .stCheckbox span,
.stRadio label, .stRadio p, .stRadio span,
[data-testid="stCheckbox"] label, [data-testid="stCheckbox"] p, [data-testid="stCheckbox"] span,
[data-testid="stRadio"] label, [data-testid="stRadio"] p, [data-testid="stRadio"] span,
div[data-testid="stVerticalBlock"] label, div[data-testid="stVerticalBlock"] p,
div[data-testid="stHorizontalBlock"] label {
    color: #374151 !important;
}

/* ── Result cards ── */
.result-card { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; margin-bottom:1rem; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,0.04); }
.result-header { padding:1rem 1.25rem; border-bottom:1px solid #F1F5F9; display:flex; align-items:center; gap:10px; background:#FAFAFA; }
.result-header-title { font-family:'Space Grotesk',sans-serif; font-size:0.9rem; font-weight:600; color:#0F172A; }

/* ── Fix white text inside expanders ── */
.streamlit-expanderHeader {
    background: #F8FAFC !important; border-radius: 10px !important;
    font-size: 0.875rem !important; font-weight: 600 !important;
    color: #0F172A !important;
}
[data-testid="stExpander"] { background: #FFFFFF !important; }
[data-testid="stExpander"] > div { background: #FFFFFF !important; }
[data-testid="stExpander"] div[role="region"] {
    background: #FFFFFF !important; color: #374151 !important;
}
[data-testid="stExpander"] div[role="region"] p,
[data-testid="stExpander"] div[role="region"] span,
[data-testid="stExpander"] div[role="region"] li,
[data-testid="stExpander"] div[role="region"] div,
[data-testid="stExpander"] div[role="region"] strong,
[data-testid="stExpander"] div[role="region"] em {
    color: #374151 !important;
    background: #FFFFFF !important;
}
/* Also fix stMarkdownContainer inside expanders */
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] span,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] li,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] {
    color: #374151 !important;
    background: transparent !important;
}

/* ── Security badge ── */
.security-active { background:#F0FDF4; border:1px solid #BBF7D0; border-radius:10px; padding:12px 16px; font-size:0.8rem; color:#15803D; margin:1rem 0; }
.required-star { color:#EF4444; font-size:0.8rem; }
.optional-tag { font-size:0.7rem; color:#94A3B8; font-style:italic; margin-left:4px; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap:4px; background:#F1F5F9; border-radius:12px; padding:4px; border:none; }
.stTabs [data-baseweb="tab"] { border-radius:8px !important; font-size:0.85rem !important; font-weight:500 !important; color:#64748B !important; padding:8px 16px !important; border:none !important; background:transparent !important; }
.stTabs [aria-selected="true"] { background:#FFFFFF !important; color:#0F172A !important; box-shadow:0 1px 3px rgba(0,0,0,0.08) !important; font-weight:600 !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] { border:2px dashed #E2E8F0 !important; border-radius:12px !important; background:#FAFAFA !important; }
hr { border:none; border-top:1px solid #F1F5F9; margin:1.5rem 0; }
.stSuccess, .stInfo, .stWarning, .stError { border-radius:10px !important; font-size:0.85rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
async def run_agent_async(agent, app_name, user_id, session_id, message, retries=3):
    ss = InMemorySessionService()
    await ss.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    runner = Runner(agent=agent, app_name=app_name, session_service=ss)
    for attempt in range(retries):
        try:
            txt = ""
            async for event in runner.run_async(
                user_id=user_id, session_id=session_id,
                new_message=types.Content(role="user", parts=[types.Part(text=message)])
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            txt += part.text
            return txt
        except Exception as e:
            err = str(e)
            if "503" in err or "429" in err or "UNAVAILABLE" in err:
                await asyncio.sleep((attempt + 1) * 10)
            else:
                raise e
    raise Exception("Max retries reached.")

def run_agent(agent, app_name, user_id, session_id, message):
    return asyncio.run(run_agent_async(agent, app_name, user_id, session_id, message))

def extract_pdf(f):
    """Extract text from PDF using pdfplumber first, then PyPDF2 as fallback."""
    try:
        file_bytes = f.read()
        if not file_bytes:
            return ""

        # Try pdfplumber first (handles most PDF types)
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages_text = []
                for page in pdf.pages:
                    text = page.extract_text()
                    if text and text.strip():
                        pages_text.append(text.strip())
                result = "\n".join(pages_text)
                if result.strip():
                    return result
        except Exception:
            pass

        # Fallback to PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                pages_text.append(text.strip())
        return "\n".join(pages_text)

    except Exception as e:
        return f"Error reading PDF: {e}"

def render_result(icon, title, content):
    st.markdown(f"""
    <div class="result-card">
        <div class="result-header">
            <span style="font-size:1.1rem">{icon}</span>
            <span class="result-header-title">{title}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    with st.expander(f"View {title}", expanded=True):
        st.markdown(f'<div style="color:#374151;background:#FFFFFF;padding:0.5rem 0">{content}</div>',
                    unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">🚀 CareerPilot AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tagline">Multi-Agent Career Development</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">Active Agents</div>', unsafe_allow_html=True)
    for n, d in [
        ("Profile Analyzer","Strengths, gaps & readiness score"),
        ("Career Planner","24-month personalized roadmap"),
        ("Resume Agent","ATS score & keyword analysis"),
        ("Project Generator","3 tailored portfolio projects"),
        ("Interview Agent","Technical & behavioral prep"),
        ("Learning Agent","GitHub-sourced study plan"),
    ]:
        st.markdown(f'<div class="agent-item"><div class="agent-dot"></div><div><div style="font-weight:500;font-size:0.82rem">{n}</div><div style="font-size:0.72rem;color:#475569">{d}</div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">Security</div>', unsafe_allow_html=True)
    for i in ["Email & phone masking","Permission system","Local data vault","No external storage"]:
        st.markdown(f'<div class="security-item">🔒 {i}</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section">Built With</div>', unsafe_allow_html=True)
    for i in ["Google ADK","Gemini 2.5 Flash Lite","Filesystem MCP","GitHub MCP","Streamlit"]:
        st.markdown(f'<div class="security-item">⚡ {i}</div>', unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:2rem 0 1rem 0;">
    <div style="font-family:'Space Grotesk',sans-serif;font-size:1.75rem;font-weight:700;color:#0F172A;letter-spacing:-0.5px">
        Career Development Report
    </div>
    <div style="font-size:0.875rem;color:#64748B;margin-top:4px">
        Fill in your profile and let 6 AI agents build your personalized career plan
    </div>
</div>
""", unsafe_allow_html=True)

# ── Check API key ─────────────────────────────────────────────────────────────
if not os.environ.get("GOOGLE_API_KEY"):
    st.error("⚠️ No API key found. Please add GOOGLE_API_KEY to your Streamlit secrets or .env file.")
    st.stop()

# ── Session state init ────────────────────────────────────────────────────────
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = 0
if "report_ready" not in st.session_state:
    st.session_state["report_ready"] = False
if "form_data" not in st.session_state:
    st.session_state["form_data"] = None

# ── Tabs ──────────────────────────────────────────────────────────────────────
# Use query params to control which tab is active
tab1, tab2, tab3 = st.tabs(["✏️  My Profile", "📊  My Report", "ℹ️  About"])

# ═══════════════════════════════════════════════════════
# TAB 1 — PROFILE
# ═══════════════════════════════════════════════════════
with tab1:

    # Show success message if report was just generated
    if st.session_state.get("report_ready"):
        st.success("✅ Your report has been generated! Click the **📊 My Report** tab above to view it.")
        if st.button("🔄 Generate New Report", key="new_report_btn"):
            st.session_state["report_ready"] = False
            st.session_state["form_data"] = None
            st.session_state.pop("profile_result", None)
            st.rerun()
        st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("""
    <div class="card">
        <div class="card-header">
            <div class="card-icon icon-blue">👤</div>
            <div>
                <div class="card-title">Personal Information</div>
                <div class="card-desc">Fields marked <span style="color:#EF4444">*</span> are required</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        st.markdown('**Full Name** <span style="color:#EF4444">*</span>', unsafe_allow_html=True)
        name = st.text_input("name", placeholder="e.g. Ahmed Al-Rashid", label_visibility="collapsed")

        st.markdown('**Current Level** <span style="color:#EF4444">*</span>', unsafe_allow_html=True)
        current_level = st.selectbox("level", [
            "— Select your level —",
            "High School Student",
            "First-year University Student",
            "Second-year University Student",
            "Third-year University Student",
            "Final-year University Student",
            "Recent Graduate",
            "Early Professional (1-2 years)",
        ], label_visibility="collapsed")

        st.markdown('**Field of Study** <span style="color:#EF4444">*</span>', unsafe_allow_html=True)
        field_of_study = st.text_input("field", placeholder="e.g. Computer Science", label_visibility="collapsed")

    with col2:
        st.markdown('**Career Goal** <span style="color:#EF4444">*</span>', unsafe_allow_html=True)
        career_goal = st.text_input("goal", placeholder="e.g. AI Engineer, Data Scientist", label_visibility="collapsed")

        st.markdown('**Current Skills** <span style="font-size:0.7rem;color:#94A3B8;font-style:italic">(optional)</span>', unsafe_allow_html=True)
        skills = st.text_area("skills", placeholder="e.g. Python basics, HTML, some math", height=106, label_visibility="collapsed")

    st.markdown('**Experience & Projects** <span style="font-size:0.7rem;color:#94A3B8;font-style:italic">(optional)</span>', unsafe_allow_html=True)
    experience = st.text_area("experience", placeholder="e.g. No internships yet. Built a calculator in Python.", height=80, label_visibility="collapsed")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── CV Upload ──
    st.markdown("""
    <div class="card-header" style="margin-bottom:1rem">
        <div class="card-icon icon-purple">📄</div>
        <div>
            <div class="card-title">Your CV / Resume <span style="font-size:0.7rem;color:#94A3B8;font-style:italic">(optional)</span></div>
            <div class="card-desc">Upload a PDF, paste text, or skip</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    cv_option = st.radio("cv", ["📎 Upload PDF", "📋 Paste Text", "⏭️ Skip CV"],
                         horizontal=True, label_visibility="collapsed")
    cv_text = ""
    if cv_option == "📎 Upload PDF":
        uploaded = st.file_uploader("pdf", type=["pdf"], label_visibility="collapsed")
        if uploaded:
            with st.spinner("Extracting text from PDF..."):
                cv_text = extract_pdf(uploaded)
            word_count = len(cv_text.split()) if cv_text and not cv_text.startswith("Error") else 0
            if word_count > 10:
                st.success(f"✅ CV extracted successfully — {word_count} words found")
                with st.expander("Preview extracted text"):
                    st.text(cv_text[:800] + "..." if len(cv_text) > 800 else cv_text)
            else:
                st.warning("⚠️ Could not extract text from this PDF. It may be image-based or scanned. Please use **Paste Text** instead.")
                cv_text = ""
    elif cv_option == "📋 Paste Text":
        cv_text = st.text_area("paste", height=180,
                               placeholder="Paste your full CV text here...",
                               label_visibility="collapsed")
    else:
        cv_text = ""
        st.info("⏭️ Skipping CV — agents will analyze your profile text only")

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Permissions & Agents ──
    pcol1, pcol2 = st.columns(2, gap="medium")
    with pcol1:
        st.markdown("""
        <div class="card-header" style="margin-bottom:0.75rem">
            <div class="card-icon icon-green">🔒</div>
            <div><div class="card-title">Data Permissions</div>
            <div class="card-desc">Approve before processing</div></div>
        </div>
        """, unsafe_allow_html=True)
        perm_profile = st.checkbox("Profile Information", value=True)
        perm_cv      = st.checkbox("CV / Resume", value=True)

    with pcol2:
        st.markdown("""
        <div class="card-header" style="margin-bottom:0.75rem">
            <div class="card-icon icon-orange">🤖</div>
            <div><div class="card-title">Select Agents</div>
            <div class="card-desc">Choose which agents to activate</div></div>
        </div>
        """, unsafe_allow_html=True)
        run_profile   = st.checkbox("🔍 Profile Analyzer", value=True)
        run_career    = st.checkbox("🗺️ Career Planner", value=True)
        run_resume    = st.checkbox("📄 Resume Agent", value=True)
        run_projects  = st.checkbox("💡 Project Generator", value=True)
        run_interview = st.checkbox("🎤 Interview Agent", value=True)
        run_learning  = st.checkbox("📚 Learning Agent", value=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Validation ──
    errors = []
    if not name:
        errors.append("Full Name is required")
    if current_level == "— Select your level —":
        errors.append("Please select your Current Level")
    if not field_of_study:
        errors.append("Field of Study is required")
    if not career_goal:
        errors.append("Career Goal is required")
    if not perm_profile:
        errors.append("Profile permission must be granted")

    if errors:
        for err in errors:
            st.markdown(f'<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:8px 12px;font-size:0.8rem;color:#DC2626;margin-bottom:4px">⚠️ {err}</div>', unsafe_allow_html=True)

    generate_btn = st.button(
        "🚀  Generate My Career Report",
        type="primary",
        use_container_width=True,
        disabled=len(errors) > 0,
    )

    if generate_btn and len(errors) == 0:
        # Save form data to session state
        st.session_state["report_ready"] = True
        st.session_state["form_data"] = {
            "name": name,
            "current_level": current_level,
            "field_of_study": field_of_study,
            "career_goal": career_goal,
            "skills": skills,
            "experience": experience,
            "cv_text": cv_text,
            "run_profile": run_profile,
            "run_career": run_career,
            "run_resume": run_resume,
            "run_projects": run_projects,
            "run_interview": run_interview,
            "run_learning": run_learning,
        }
        st.rerun()

# ═══════════════════════════════════════════════════════
# TAB 2 — REPORT
# ═══════════════════════════════════════════════════════
with tab2:
    if not st.session_state.get("report_ready") or not st.session_state.get("form_data"):
        # Empty state
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem">
            <div style="font-size:3rem;margin-bottom:1rem">📊</div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:1.25rem;font-weight:600;color:#0F172A;margin-bottom:8px">
                No report yet
            </div>
            <div style="font-size:0.875rem;color:#64748B;max-width:400px;margin:0 auto">
                Go to the <strong>✏️ My Profile</strong> tab, fill in your details,
                and click <strong>Generate My Career Report</strong>.
                Your results will appear here automatically.
            </div>
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;max-width:700px;margin:2rem auto">
            <div class="card" style="text-align:center;padding:1.25rem"><div style="font-size:1.5rem;margin-bottom:8px">🔍</div><div style="font-size:0.8rem;font-weight:600;color:#0F172A">Profile Analysis</div><div style="font-size:0.75rem;color:#64748B;margin-top:4px">Readiness score & gaps</div></div>
            <div class="card" style="text-align:center;padding:1.25rem"><div style="font-size:1.5rem;margin-bottom:8px">🗺️</div><div style="font-size:0.8rem;font-weight:600;color:#0F172A">Career Roadmap</div><div style="font-size:0.75rem;color:#64748B;margin-top:4px">24-month action plan</div></div>
            <div class="card" style="text-align:center;padding:1.25rem"><div style="font-size:1.5rem;margin-bottom:8px">📄</div><div style="font-size:0.8rem;font-weight:600;color:#0F172A">Resume Review</div><div style="font-size:0.75rem;color:#64748B;margin-top:4px">ATS score & improvements</div></div>
            <div class="card" style="text-align:center;padding:1.25rem"><div style="font-size:1.5rem;margin-bottom:8px">💡</div><div style="font-size:0.8rem;font-weight:600;color:#0F172A">Project Ideas</div><div style="font-size:0.75rem;color:#64748B;margin-top:4px">3 tailored projects</div></div>
            <div class="card" style="text-align:center;padding:1.25rem"><div style="font-size:1.5rem;margin-bottom:8px">🎤</div><div style="font-size:0.8rem;font-weight:600;color:#0F172A">Interview Prep</div><div style="font-size:0.75rem;color:#64748B;margin-top:4px">12 tailored questions</div></div>
            <div class="card" style="text-align:center;padding:1.25rem"><div style="font-size:1.5rem;margin-bottom:8px">📚</div><div style="font-size:0.8rem;font-weight:600;color:#0F172A">Learning Plan</div><div style="font-size:0.75rem;color:#64748B;margin-top:4px">Real GitHub resources</div></div>
        </div>
        """, unsafe_allow_html=True)

    else:
        fd = st.session_state["form_data"]

        # ── Header ──
        st.markdown(f"""
        <div style="background:#0F172A;border-radius:16px;padding:1.5rem;margin-bottom:1.5rem">
            <div style="font-family:'Space Grotesk',sans-serif;font-size:1.2rem;font-weight:700;color:#FFFFFF">
                📊 Career Report — {fd['name']}
            </div>
            <div style="font-size:0.8rem;color:#94A3B8;margin-top:4px">
                Target: {fd['career_goal']} · Level: {fd['current_level']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Security ──
        user_input = f"My name is {fd['name']}. I am a {fd['current_level']} studying {fd['field_of_study']}."
        if fd['skills']:
            user_input += f" Skills: {fd['skills']}."
        if fd['experience']:
            user_input += f" Experience: {fd['experience']}."
        user_input += f" Career goal: {fd['career_goal']}."

        if fd['cv_text']:
            masked_cv, cv_vault = mask_personal_data(fd['cv_text'])
        else:
            masked_cv, cv_vault = "", {}
        masked_profile, profile_vault = mask_personal_data(user_input)
        vault = {**cv_vault, **profile_vault}

        if vault:
            items = " · ".join([f"{k} → {v[:3]}***" for k, v in vault.items()])
            st.markdown(f'<div class="security-active">🛡️ Security Layer Active — Protected: {items}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="security-active">✅ Security Layer Active — No sensitive PII detected</div>', unsafe_allow_html=True)

        app_name = "careerpilot_ai"
        user_id  = "user_001"

        # ── Run agents ──
        if fd["run_profile"]:
            with st.spinner("🔍 Agent 1: Analyzing your profile..."):
                try:
                    profile_result = run_agent(profile_analyzer, app_name, user_id, "s001", masked_profile)
                    st.session_state["profile_result"] = profile_result
                    render_result("🔍", "Profile Analysis", profile_result)
                    st.success("✅ Profile analysis complete")
                except Exception as e:
                    st.error(f"Profile analysis failed: {e}")
                    st.stop()

        if fd["run_career"]:
            with st.spinner("🗺️ Agent 2: Building career roadmap..."):
                try:
                    result = run_agent(career_planner, app_name, user_id, "s002",
                        f"Profile: {masked_profile}\nAnalysis: {st.session_state.get('profile_result','')}\nCreate roadmap.")
                    render_result("🗺️", "Career Roadmap", result)
                    st.success("✅ Career roadmap complete")
                except Exception as e:
                    st.error(f"Career planning failed: {e}")

        if fd["run_resume"]:
            with st.spinner("📄 Agent 3: Reviewing resume..."):
                try:
                    cv_section = f"\nCV: {masked_cv}" if masked_cv else "\nNo CV provided — give general advice based on profile."
                    result = run_agent(resume_agent, app_name, user_id, "s003",
                        f"Profile: {masked_profile}\nTarget: {fd['career_goal']}{cv_section}")
                    render_result("📄", "Resume Analysis", result)
                    st.success("✅ Resume analysis complete")
                except Exception as e:
                    st.error(f"Resume review failed: {e}")

        if fd["run_projects"]:
            with st.spinner("💡 Agent 4: Generating project ideas..."):
                try:
                    result = run_agent(project_generator, app_name, user_id, "s004",
                        f"Profile: {masked_profile}\nAnalysis: {st.session_state.get('profile_result','')}\nSuggest 3 projects for {fd['career_goal']}.")
                    render_result("💡", "Project Suggestions", result)
                    st.success("✅ Project suggestions complete")
                except Exception as e:
                    st.error(f"Project generation failed: {e}")

        if fd["run_interview"]:
            with st.spinner("🎤 Agent 5: Generating interview guide..."):
                try:
                    result = run_agent(interview_agent, app_name, user_id, "s005",
                        f"Profile: {masked_profile}\nAnalysis: {st.session_state.get('profile_result','')}\nTarget: {fd['career_goal']}\nGenerate interview guide.")
                    render_result("🎤", "Interview Preparation", result)
                    st.success("✅ Interview guide complete")
                except Exception as e:
                    st.error(f"Interview prep failed: {e}")

        if fd["run_learning"]:
            with st.spinner("📚 Agent 6: Building learning plan..."):
                try:
                    result = run_agent(learning_agent, app_name, user_id, "s006",
                        f"Profile: {masked_profile}\nSkill gaps: {st.session_state.get('profile_result','')}\nTarget: {fd['career_goal']}\nBuild personalized learning plan.")
                    render_result("📚", "Personalized Learning Plan", result)
                    st.success("✅ Learning plan complete")
                except Exception as e:
                    st.error(f"Learning plan failed: {e}")

        # ── Done ──
        st.balloons()
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0F172A,#1E293B);border-radius:16px;padding:1.5rem;text-align:center;margin-top:1.5rem">
            <div style="font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;color:#FFFFFF;margin-bottom:4px">
                🎉 Your CareerPilot Report is Complete!
            </div>
            <div style="font-size:0.8rem;color:#94A3B8">
                Expand each section above to read your full results
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Start Over — Generate New Report", key="restart"):
            st.session_state["report_ready"] = False
            st.session_state["form_data"] = None
            st.session_state.pop("profile_result", None)
            st.rerun()

# ═══════════════════════════════════════════════════════
# TAB 3 — ABOUT
# ═══════════════════════════════════════════════════════
with tab3:
    st.markdown("""
    <div class="card">
        <div class="card-header">
            <div class="card-icon icon-blue">🚀</div>
            <div><div class="card-title">About CareerPilot AI</div>
            <div class="card-desc">Multi-Agent Career Development Platform</div></div>
        </div>
        <div style="font-size:0.875rem;color:#374151;line-height:1.7">
            CareerPilot AI is a multi-agent system built with Google ADK that helps students and early
            professionals navigate their career journey using 6 specialized AI agents, dual MCP servers,
            and a security layer. Built for the
            <strong>Kaggle 5-Day AI Agents Capstone — Agents for Good track</strong>.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.code("""
User Input  →  Security Layer  →  MCP Servers  →  Agent Pipeline  →  Report
Security:   PII Masking · Permission System · Data Vault
MCP:        Filesystem MCP · GitHub MCP
Agents:     Profile Analyzer → Career Planner → Resume Agent
            → Project Generator → Interview Agent → Learning Agent
    """, language="text")

    c1, c2, c3 = st.columns(3)
    for col, num, lbl in zip([c1,c2,c3],["6","2","3"],["AI Agents","MCP Servers","Security Layers"]):
        with col:
            st.markdown(f'<div class="card" style="text-align:center"><div style="font-size:1.75rem;font-weight:700;color:#0F172A;font-family:Space Grotesk,sans-serif">{num}</div><div style="font-size:0.8rem;color:#64748B;margin-top:4px">{lbl}</div></div>', unsafe_allow_html=True)