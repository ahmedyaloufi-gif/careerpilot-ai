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
import re

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
#MainMenu, footer { visibility: hidden; }
header { visibility: hidden; }
[data-testid="collapsedControl"] { visibility: visible !important; opacity: 1 !important; }
.block-container { padding: 0 2rem 2rem 2rem !important; max-width: 1200px; }

[data-testid="stSidebar"] { background: #0F1117 !important; border-right: 1px solid #1E2130; }
.sidebar-logo { font-family:'Space Grotesk',sans-serif; font-size:1.4rem; font-weight:700; color:#FFFFFF; padding:1.5rem 0 0.5rem 0; }
.sidebar-tagline { font-size:0.75rem; color:#64748B; margin-bottom:2rem; }
.sidebar-section { font-size:0.65rem; font-weight:600; letter-spacing:1.5px; text-transform:uppercase; color:#475569; margin:1.5rem 0 0.75rem 0; }
.agent-item { display:flex; align-items:center; gap:10px; padding:8px 12px; border-radius:8px; margin-bottom:4px; font-size:0.85rem; color:#CBD5E1; }
.agent-item:hover { background:#1E2130; }
.agent-dot { width:6px; height:6px; border-radius:50%; background:#3B82F6; flex-shrink:0; }
.security-item { display:flex; align-items:center; gap:8px; font-size:0.8rem; color:#94A3B8; padding:4px 0; }

.card { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; padding:1.5rem; margin-bottom:1.25rem; box-shadow:0 1px 3px rgba(0,0,0,0.04); }
.card-header { display:flex; align-items:center; gap:10px; margin-bottom:1.25rem; }
.card-icon { width:36px; height:36px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:1rem; flex-shrink:0; }
.icon-blue{background:#EFF6FF;} .icon-purple{background:#F5F3FF;}
.icon-green{background:#F0FDF4;} .icon-orange{background:#FFF7ED;}
.card-title { font-family:'Space Grotesk',sans-serif; font-size:0.95rem; font-weight:600; color:#0F172A; }
.card-desc { font-size:0.8rem; color:#64748B; margin-top:1px; }

.stButton > button[kind="primary"] {
    background:#0F172A !important; color:#FFFFFF !important; border:none !important;
    border-radius:10px !important; padding:0.65rem 1.5rem !important;
    font-size:0.875rem !important; font-weight:600 !important;
    transition:all 0.15s !important; box-shadow:0 1px 2px rgba(0,0,0,0.1) !important;
}
.stButton > button[kind="primary"]:hover { background:#1E293B !important; transform:translateY(-1px) !important; }
.stButton > button[kind="primary"]:disabled { background:#94A3B8 !important; cursor:not-allowed !important; transform:none !important; }
.stButton > button { border-radius:10px !important; font-weight:500 !important; }

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

label, .stCheckbox label, .stCheckbox p, .stCheckbox span,
.stRadio label, .stRadio p, .stRadio span,
[data-testid="stCheckbox"] label, [data-testid="stCheckbox"] p, [data-testid="stCheckbox"] span,
[data-testid="stRadio"] label, [data-testid="stRadio"] p, [data-testid="stRadio"] span,
div[data-testid="stVerticalBlock"] label, div[data-testid="stVerticalBlock"] p,
div[data-testid="stHorizontalBlock"] label { color: #374151 !important; }

.result-card { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; margin-bottom:1rem; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,0.04); }
.result-header { padding:1rem 1.25rem; border-bottom:1px solid #F1F5F9; display:flex; align-items:center; gap:10px; background:#FAFAFA; }
.result-header-title { font-family:'Space Grotesk',sans-serif; font-size:0.9rem; font-weight:600; color:#0F172A; }

.streamlit-expanderHeader { background:#F8FAFC !important; border-radius:10px !important; font-size:0.875rem !important; font-weight:600 !important; color:#0F172A !important; }
[data-testid="stExpander"] { background:#FFFFFF !important; }
[data-testid="stExpander"] > div { background:#FFFFFF !important; }
[data-testid="stExpander"] div[role="region"] { background:#FFFFFF !important; color:#374151 !important; }
[data-testid="stExpander"] div[role="region"] p,
[data-testid="stExpander"] div[role="region"] span,
[data-testid="stExpander"] div[role="region"] li,
[data-testid="stExpander"] div[role="region"] div,
[data-testid="stExpander"] div[role="region"] strong,
[data-testid="stExpander"] div[role="region"] em { color:#374151 !important; background:#FFFFFF !important; }
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] span,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] li,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] { color:#374151 !important; background:transparent !important; }

.security-active { background:#F0FDF4; border:1px solid #BBF7D0; border-radius:10px; padding:12px 16px; font-size:0.8rem; color:#15803D; margin:1rem 0; }

/* ── Interview chat ── */
.chat-container { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; padding:1.5rem; margin-bottom:1rem; }
.chat-msg-user { background:#0F172A; color:#FFFFFF; border-radius:12px 12px 4px 12px; padding:10px 14px; margin:8px 0 8px 20%; font-size:0.875rem; }
.chat-msg-ai { background:#F1F5F9; color:#0F172A; border-radius:12px 12px 12px 4px; padding:10px 14px; margin:8px 20% 8px 0; font-size:0.875rem; }
.chat-label-user { text-align:right; font-size:0.7rem; color:#94A3B8; margin-bottom:2px; }
.chat-label-ai { font-size:0.7rem; color:#94A3B8; margin-bottom:2px; }

/* ── Agent badge ── */
.agent-badge { display:inline-flex; align-items:center; gap:6px; background:#EFF6FF; border:1px solid #BFDBFE; border-radius:100px; padding:4px 12px; font-size:0.75rem; color:#1D4ED8; font-weight:500; margin:3px; }
.agent-badge.skipped { background:#F1F5F9; border-color:#E2E8F0; color:#94A3B8; }

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
    try:
        file_bytes = f.read()
        if not file_bytes:
            return ""
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
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                pages_text.append(text.strip())
        return "\n".join(pages_text)
    except Exception as e:
        return f"Error reading PDF: {e}"

def make_links_clickable(text):
    """Convert plain URLs in text to clickable markdown links."""
    url_pattern = r'(https?://[^\s\)\]]+)'
    def replace_url(m):
        url = m.group(1).rstrip('.,;')
        # Try to get a short name from the URL
        parts = url.replace('https://','').replace('http://','').split('/')
        if len(parts) >= 2 and parts[0] == 'github.com':
            label = f"{parts[1]}/{parts[2]}" if len(parts) > 2 else parts[1]
        else:
            label = parts[0]
        return f"[🔗 {label}]({url})"
    return re.sub(url_pattern, replace_url, text)

def render_result(icon, title, content, make_links=False):
    if make_links:
        content = make_links_clickable(content)
    st.markdown(f"""
    <div class="result-card">
        <div class="result-header">
            <span style="font-size:1.1rem">{icon}</span>
            <span class="result-header-title">{title}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    with st.expander(f"View {title}", expanded=True):
        st.markdown(content)

def decide_agents(fd):
    """
    Smart agent selection — decides which agents to run based on user profile.
    Returns a dict of agent_name -> (should_run: bool, reason: str)
    """
    has_cv       = bool(fd.get("cv_text", "").strip())
    has_skills   = bool(fd.get("skills", "").strip())
    has_exp      = bool(fd.get("experience", "").strip())
    level        = fd.get("current_level", "")
    goal         = fd.get("career_goal", "").lower()

    is_student   = any(x in level.lower() for x in ["student", "high school"])
    is_early     = "early professional" in level.lower() or "recent graduate" in level.lower()
    is_technical = any(x in goal for x in ["engineer","developer","scientist","analyst","programmer","architect","ml","ai","data"])

    agents = {}

    # Profile Analyzer — always run
    agents["profile"] = (True, "Always runs to assess your current situation")

    # Career Planner — always run
    agents["career"] = (True, "Always runs to build your roadmap")

    # Resume Agent — only if CV provided OR early professional
    if has_cv:
        agents["resume"] = (True, "You uploaded a CV — reviewing it for ATS compatibility")
    elif is_early:
        agents["resume"] = (True, "As an early professional, CV advice is critical")
    else:
        agents["resume"] = (False, "Skipped — no CV uploaded. Upload a CV to get ATS feedback")

    # Project Generator — run for students or if no experience
    if is_student or not has_exp:
        agents["projects"] = (True, "Building projects is your #1 priority to fill experience gaps")
    elif is_technical:
        agents["projects"] = (True, "Technical roles require a strong project portfolio")
    else:
        agents["projects"] = (False, "Skipped — your experience level suggests you may already have portfolio projects")

    # Interview Agent — always run for job seekers
    agents["interview"] = (True, "Interview preparation is essential for any career goal")

    # Learning Agent — run for students or those with skill gaps
    if is_student or not has_skills:
        agents["learning"] = (True, "Building a structured learning plan to close your skill gaps")
    elif is_technical:
        agents["learning"] = (True, "Technical roles require continuous learning — building your study plan")
    else:
        agents["learning"] = (False, "Skipped — your profile suggests you have sufficient learning resources")

    return agents

# ── Session state init ────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "active_tab": "profile",
        "report_ready": False,
        "form_data": None,
        "report_results": {},   # stores each agent's output text
        "interview_mode": False,
        "interview_choice": None,  # "start" | "improve"
        "interview_messages": [],  # full conversation history
        "interview_session_id": "interview_session_001",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

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
        Fill in your profile and let AI agents build your personalized career plan
    </div>
</div>
""", unsafe_allow_html=True)

if not os.environ.get("GOOGLE_API_KEY"):
    st.error("⚠️ No API key found. Please add GOOGLE_API_KEY to your Streamlit secrets or .env file.")
    st.stop()

# ── Manual Tab Bar ────────────────────────────────────────────────────────────
_t = st.session_state["active_tab"]
_tc1, _tc2, _tc3 = st.columns(3)
with _tc1:
    if st.button("✏️  My Profile", use_container_width=True,
                 type="primary" if _t == "profile" else "secondary", key="tab_profile"):
        st.session_state["active_tab"] = "profile"
        st.rerun()
with _tc2:
    if st.button("📊  My Report", use_container_width=True,
                 type="primary" if _t == "report" else "secondary", key="tab_report"):
        st.session_state["active_tab"] = "report"
        st.rerun()
with _tc3:
    if st.button("ℹ️  About", use_container_width=True,
                 type="primary" if _t == "about" else "secondary", key="tab_about"):
        st.session_state["active_tab"] = "about"
        st.rerun()

st.markdown("<hr style='margin:0.5rem 0 1.5rem 0'>", unsafe_allow_html=True)

# ═══════════════════════════════════════
# TAB 1 — PROFILE
# ═══════════════════════════════════════
if st.session_state["active_tab"] == "profile":

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
                st.success(f"✅ CV extracted — {word_count} words found")
                with st.expander("Preview"):
                    st.text(cv_text[:800] + "..." if len(cv_text) > 800 else cv_text)
            else:
                st.warning("⚠️ Could not extract text. PDF may be image-based. Please use **Paste Text** instead.")
                cv_text = ""
    elif cv_option == "📋 Paste Text":
        cv_text = st.text_area("paste", height=180, placeholder="Paste your full CV text here...", label_visibility="collapsed")
    else:
        st.info("⏭️ Skipping CV — agents will analyze your profile only")

    st.markdown("<hr>", unsafe_allow_html=True)

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
            <div><div class="card-title">Smart Agent Selection</div>
            <div class="card-desc">AI will choose the right agents for you</div></div>
        </div>
        """, unsafe_allow_html=True)
        st.info("🧠 After you click Generate, the system will automatically decide which agents are most relevant for your profile — no manual selection needed.")

    st.markdown("<br>", unsafe_allow_html=True)

    errors = []
    if not name: errors.append("Full Name is required")
    if current_level == "— Select your level —": errors.append("Please select your Current Level")
    if not field_of_study: errors.append("Field of Study is required")
    if not career_goal: errors.append("Career Goal is required")
    if not perm_profile: errors.append("Profile permission must be granted")

    for err in errors:
        st.markdown(f'<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:8px 12px;font-size:0.8rem;color:#DC2626;margin-bottom:4px">⚠️ {err}</div>', unsafe_allow_html=True)

    generate_btn = st.button(
        "🚀  Generate My Career Report",
        type="primary",
        use_container_width=True,
        disabled=len(errors) > 0,
    )

    if generate_btn and len(errors) == 0:
        st.session_state["report_ready"] = True
        st.session_state["report_results"] = {}  # clear old results
        st.session_state["interview_mode"] = False
        st.session_state["interview_choice"] = None
        st.session_state["interview_messages"] = []
        st.session_state["active_tab"] = "report"
        st.session_state["form_data"] = {
            "name": name, "current_level": current_level,
            "field_of_study": field_of_study, "career_goal": career_goal,
            "skills": skills, "experience": experience, "cv_text": cv_text,
        }
        st.rerun()

# ═══════════════════════════════════════
# TAB 2 — REPORT
# ═══════════════════════════════════════
elif st.session_state["active_tab"] == "report":

    if not st.session_state.get("report_ready") or not st.session_state.get("form_data"):
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem">
            <div style="font-size:3rem;margin-bottom:1rem">📊</div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:1.25rem;font-weight:600;color:#0F172A;margin-bottom:8px">No report yet</div>
            <div style="font-size:0.875rem;color:#64748B;max-width:400px;margin:0 auto">
                Go to <strong>✏️ My Profile</strong>, fill in your details,
                and click <strong>Generate My Career Report</strong>.
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
        results = st.session_state["report_results"]

        # ── Report header ──
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

        # ── Security masking ──
        user_input = f"My name is {fd['name']}. I am a {fd['current_level']} studying {fd['field_of_study']}."
        if fd.get('skills'): user_input += f" Skills: {fd['skills']}."
        if fd.get('experience'): user_input += f" Experience: {fd['experience']}."
        user_input += f" Career goal: {fd['career_goal']}."

        masked_cv, cv_vault = mask_personal_data(fd['cv_text']) if fd.get('cv_text') else ("", {})
        masked_profile, profile_vault = mask_personal_data(user_input)
        vault = {**cv_vault, **profile_vault}

        if vault:
            items = " · ".join([f"{k} → {v[:3]}***" for k, v in vault.items()])
            st.markdown(f'<div class="security-active">🛡️ Security Layer Active — Protected: {items}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="security-active">✅ Security Layer Active — No sensitive PII detected</div>', unsafe_allow_html=True)

        # ── Decide which agents to run ──
        agent_plan = decide_agents(fd)

        # Show agent plan
        st.markdown('<div style="margin:0.75rem 0;font-size:0.8rem;color:#64748B;font-weight:500">🧠 Smart Agent Selection:</div>', unsafe_allow_html=True)
        badges = ""
        for agent_key, (should_run, reason) in agent_plan.items():
            icons = {"profile":"🔍","career":"🗺️","resume":"📄","projects":"💡","interview":"🎤","learning":"📚"}
            names = {"profile":"Profile","career":"Career","resume":"Resume","projects":"Projects","interview":"Interview","learning":"Learning"}
            cls = "agent-badge" if should_run else "agent-badge skipped"
            badges += f'<span class="{cls}">{icons[agent_key]} {names[agent_key]}</span>'
        st.markdown(f'<div style="margin-bottom:1rem">{badges}</div>', unsafe_allow_html=True)

        app_name = "careerpilot_ai"
        user_id  = "user_001"

        # ── Run agents — only if not already run (persistence) ──

        # ── Agent 1: Profile Analyzer ──────────────────────
        if agent_plan["profile"][0]:
            if "profile" not in results:
                with st.spinner("🔍 Agent 1: Analyzing your profile..."):
                    try:
                        r = run_agent(profile_analyzer, app_name, user_id, "s001", masked_profile)
                        results["profile"] = r
                        st.session_state["report_results"] = results
                    except Exception as e:
                        st.error(f"Profile analysis failed: {e}"); st.stop()
            render_result("🔍", "Profile Analysis", results["profile"])

        # ── Agent 2: Resume Agent ───────────────────────────
        if agent_plan["resume"][0]:
            if "resume" not in results:
                with st.spinner("📄 Agent 2: Reviewing resume..."):
                    try:
                        cv_section = f"\nCV: {masked_cv}" if masked_cv else "\nNo CV — give general advice."
                        r = run_agent(resume_agent, app_name, user_id, "s003",
                            f"Profile: {masked_profile}\nTarget: {fd['career_goal']}{cv_section}")
                        results["resume"] = r
                        st.session_state["report_results"] = results
                    except Exception as e:
                        st.error(f"Resume review failed: {e}")
            if "resume" in results:
                render_result("📄", "Resume Analysis", results["resume"])
        else:
            st.info(f"📄 Resume Agent: {agent_plan['resume'][1]}")

        # ── Agent 3: Project Generator ──────────────────────
        if agent_plan["projects"][0]:
            if "projects" not in results:
                with st.spinner("💡 Agent 3: Generating project ideas..."):
                    try:
                        r = run_agent(project_generator, app_name, user_id, "s004",
                            f"Profile: {masked_profile}\nAnalysis: {results.get('profile','')}\nSuggest 3 projects for {fd['career_goal']}.")
                        results["projects"] = r
                        st.session_state["report_results"] = results
                    except Exception as e:
                        st.error(f"Project generation failed: {e}")
            if "projects" in results:
                render_result("💡", "Project Suggestions", results["projects"])
        else:
            st.info(f"💡 Project Generator: {agent_plan['projects'][1]}")

        # ── Agent 4: Interview Agent ────────────────────────
        if agent_plan["interview"][0]:
            if "interview" not in results:
                with st.spinner("🎤 Agent 4: Generating interview guide..."):
                    try:
                        r = run_agent(interview_agent, app_name, user_id, "s005",
                            f"Profile: {masked_profile}\nAnalysis: {results.get('profile','')}\nTarget: {fd['career_goal']}\nGenerate interview guide.")
                        results["interview"] = r
                        st.session_state["report_results"] = results
                    except Exception as e:
                        st.error(f"Interview prep failed: {e}")
            if "interview" in results:
                render_result("🎤", "Interview Preparation", results["interview"])

        # ── Agent 5: Career Planner ─────────────────────────
        if agent_plan["career"][0]:
            if "career" not in results:
                with st.spinner("🗺️ Agent 5: Building career roadmap..."):
                    try:
                        r = run_agent(career_planner, app_name, user_id, "s002",
                            f"Profile: {masked_profile}\nAnalysis: {results.get('profile','')}\nCreate roadmap.")
                        results["career"] = r
                        st.session_state["report_results"] = results
                    except Exception as e:
                        st.error(f"Career planning failed: {e}")
            if "career" in results:
                render_result("🗺️", "Career Roadmap", results["career"])

        # ── Agent 6: Learning Agent ─────────────────────────
        if agent_plan["learning"][0]:
            if "learning" not in results:
                with st.spinner("📚 Agent 6: Building learning plan..."):
                    try:
                        r = run_agent(learning_agent, app_name, user_id, "s006",
                            f"Profile: {masked_profile}\nSkill gaps: {results.get('profile','')}\nTarget: {fd['career_goal']}\nBuild learning plan with real GitHub links.")
                        results["learning"] = r
                        st.session_state["report_results"] = results
                    except Exception as e:
                        st.error(f"Learning plan failed: {e}")
            if "learning" in results:
                render_result("📚", "Personalized Learning Plan", results["learning"], make_links=True)
        else:
            st.info(f"📚 Learning Agent: {agent_plan['learning'][1]}")
        # ── Report complete banner ──
        if len(results) > 0:
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

            # ── Interview Practice button ──
            if "interview" in results and not st.session_state.get("interview_mode"):
                st.markdown("""
                <div class="card">
                    <div class="card-header">
                        <div class="card-icon icon-blue">🎤</div>
                        <div>
                            <div class="card-title">Ready to Practice Your Interview?</div>
                            <div class="card-desc">Practice with an AI interviewer based on your profile and target role</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                ic1, ic2 = st.columns(2, gap="medium")
                with ic1:
                    if st.button("🎤 Start Interview Practice", type="primary", use_container_width=True, key="start_interview"):
                        st.session_state["interview_mode"] = True
                        st.session_state["interview_choice"] = "start"
                        st.session_state["interview_messages"] = []
                        st.rerun()
                with ic2:
                    if st.button("📝 Improve My CV First", use_container_width=True, key="improve_cv"):
                        st.session_state["active_tab"] = "profile"
                        st.rerun()

            # ── Interview Chat ──
            if st.session_state.get("interview_mode"):
                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown("""
                <div style="font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:700;color:#0F172A;margin-bottom:1rem">
                    🎤 Interview Practice Room
                </div>
                """, unsafe_allow_html=True)

                st.info(f"You are being interviewed for: **{fd['career_goal']}** — Answer naturally, as you would in a real interview.")

                # Display chat history
                messages = st.session_state["interview_messages"]

                if not messages:
                    # First message from AI interviewer
                    opening = (
                        f"Hello {fd['name']}! I'm your AI interviewer today. "
                        f"You're interviewing for a {fd['career_goal']} position. "
                        f"Let's begin. Tell me a little about yourself and why you're interested in this role."
                    )
                    messages.append({"role": "ai", "text": opening})
                    st.session_state["interview_messages"] = messages

                # Render chat messages
                for msg in messages:
                    if msg["role"] == "user":
                        st.markdown(f'<div class="chat-label-user">You</div><div class="chat-msg-user">{msg["text"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-label-ai">🤖 Interviewer</div><div class="chat-msg-ai">{msg["text"]}</div>', unsafe_allow_html=True)

                # User input
                st.markdown("<br>", unsafe_allow_html=True)
                user_answer = st.text_area("Your answer", placeholder="Type your answer here...",
                                           height=100, key=f"chat_input_{len(messages)}",
                                           label_visibility="collapsed")

                send_col, end_col = st.columns([3, 1])
                with send_col:
                    send_btn = st.button("Send Answer ➤", type="primary", use_container_width=True, key="send_answer")
                with end_col:
                    end_btn = st.button("End Interview", use_container_width=True, key="end_interview")

                if send_btn and user_answer.strip():
                    messages.append({"role": "user", "text": user_answer.strip()})

                    # Build conversation context
                    convo = "\n".join([
                        f"{'Candidate' if m['role']=='user' else 'Interviewer'}: {m['text']}"
                        for m in messages
                    ])

                    interview_prompt = f"""
You are a professional interviewer conducting a real job interview.
The candidate is: {fd['name']}, a {fd['current_level']} targeting {fd['career_goal']}.
Their skills: {fd.get('skills','Not provided')}.
Their experience: {fd.get('experience','Not provided')}.

Conversation so far:
{convo}

Continue the interview naturally. Ask the next relevant question based on their answer.
Give brief encouraging feedback on their answer (1 sentence), then ask your next question.
Keep responses concise — under 100 words total.
Do NOT end the interview unless the candidate asks to stop.
"""
                    with st.spinner("Interviewer is thinking..."):
                        try:
                            session_id = f"interview_{len(messages)}"
                            ai_response = run_agent(interview_agent, app_name, user_id, session_id, interview_prompt)
                            messages.append({"role": "ai", "text": ai_response})
                            st.session_state["interview_messages"] = messages
                        except Exception as e:
                            st.error(f"Interview error: {e}")
                    st.rerun()

                if end_btn:
                    messages.append({"role": "ai", "text": f"Thank you for the interview, {fd['name']}! You did well. Keep practicing and reviewing your responses. Good luck with your career journey! 🎉"})
                    st.session_state["interview_messages"] = messages
                    st.session_state["interview_mode"] = False
                    st.rerun()

            # ── Start Over ──
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Start Over — Generate New Report", key="restart"):
                st.session_state["report_ready"] = False
                st.session_state["form_data"] = None
                st.session_state["report_results"] = {}
                st.session_state["active_tab"] = "profile"
                st.session_state["interview_mode"] = False
                st.session_state["interview_messages"] = []
                st.session_state.pop("profile_result", None)
                st.rerun()

# ═══════════════════════════════════════
# TAB 3 — ABOUT
# ═══════════════════════════════════════
elif st.session_state["active_tab"] == "about":
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
User Input  →  Security Layer  →  Smart Agent Selection  →  Agent Pipeline  →  Report
Security:   PII Masking · Permission System · Data Vault
MCP:        Filesystem MCP · GitHub MCP
Agents:     Profile Analyzer → Career Planner → Resume Agent (if CV)
            → Project Generator (if student) → Interview Agent → Learning Agent
    """, language="text")

    c1, c2, c3 = st.columns(3)
    for col, num, lbl in zip([c1,c2,c3],["6","2","3"],["AI Agents","MCP Servers","Security Layers"]):
        with col:
            st.markdown(f'<div class="card" style="text-align:center"><div style="font-size:1.75rem;font-weight:700;color:#0F172A">{num}</div><div style="font-size:0.8rem;color:#64748B;margin-top:4px">{lbl}</div></div>', unsafe_allow_html=True)