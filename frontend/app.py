import streamlit as st
import asyncio
import sys
import os
 
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
from tools.security import mask_personal_data, get_security_report
import PyPDF2
import io
 
# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CareerPilot AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)
 
# ── Design System ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
 
/* ── Reset & Base ── */
* { box-sizing: border-box; }
 
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
 
.stApp {
    background-color: #F7F8FA;
}
 
/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 0 2rem 2rem 2rem !important;
    max-width: 1200px;
}
 
/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0F1117 !important;
    border-right: 1px solid #1E2130;
}
[data-testid="stSidebar"] .sidebar-logo,
[data-testid="stSidebar"] .sidebar-tagline,
[data-testid="stSidebar"] .sidebar-section,
[data-testid="stSidebar"] .agent-item,
[data-testid="stSidebar"] .security-item {
    color: #E2E8F0 !important;
}
 
.sidebar-logo {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #FFFFFF !important;
    letter-spacing: -0.5px;
    padding: 1.5rem 0 0.5rem 0;
}
 
.sidebar-tagline {
    font-size: 0.75rem;
    color: #64748B !important;
    margin-bottom: 2rem;
    font-weight: 400;
}
 
.sidebar-section {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #475569 !important;
    margin: 1.5rem 0 0.75rem 0;
}
 
.agent-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    border-radius: 8px;
    margin-bottom: 4px;
    font-size: 0.85rem;
    color: #CBD5E1 !important;
    transition: background 0.15s;
}
 
.agent-item:hover {
    background: #1E2130;
}
 
.agent-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #3B82F6;
    flex-shrink: 0;
}
 
.security-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    color: #94A3B8 !important;
    padding: 4px 0;
}
 
/* ── Top Header Bar ── */
.top-bar {
    background: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    padding: 1rem 0;
    margin-bottom: 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
 
.page-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: #0F172A;
    letter-spacing: -0.5px;
}
 
.page-subtitle {
    font-size: 0.85rem;
    color: #64748B;
    margin-top: 2px;
}
 
/* ── Cards ── */
.card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
 
.card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 1.25rem;
}
 
.card-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
}
 
.icon-blue   { background: #EFF6FF; }
.icon-purple { background: #F5F3FF; }
.icon-green  { background: #F0FDF4; }
.icon-orange { background: #FFF7ED; }
 
.card-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.95rem;
    font-weight: 600;
    color: #0F172A;
}
 
.card-desc {
    font-size: 0.8rem;
    color: #64748B;
    margin-top: 1px;
}
 
/* ── Stat pills ── */
.stat-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}
 
.stat-pill {
    background: #F1F5F9;
    border: 1px solid #E2E8F0;
    border-radius: 100px;
    padding: 4px 12px;
    font-size: 0.75rem;
    color: #475569;
    font-weight: 500;
}
 
/* ── Primary Button ── */
.stButton > button[kind="primary"] {
    background: #0F172A !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 1.5rem !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.2px !important;
    transition: all 0.15s !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
}
 
.stButton > button[kind="primary"]:hover {
    background: #1E293B !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(15,23,42,0.2) !important;
}
 
/* ── Secondary Button ── */
.stButton > button {
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
}
 
/* ── Form Fields ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    border-radius: 10px !important;
    border: 1px solid #E2E8F0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
    color: #0F172A !important;
    background: #FFFFFF !important;
}
 
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1) !important;
}
 
label {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: #374151 !important;
    letter-spacing: 0.1px;
}
 
/* ── Progress / Status ── */
.step-status {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    border-radius: 10px;
    margin-bottom: 8px;
    font-size: 0.85rem;
    font-weight: 500;
}
 
.step-pending {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    color: #94A3B8;
}
 
.step-running {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    color: #1D4ED8;
}
 
.step-done {
    background: #F0FDF4;
    border: 1px solid #BBF7D0;
    color: #15803D;
}
 
/* ── Result Cards ── */
.result-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    margin-bottom: 1rem;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
 
.result-header {
    padding: 1rem 1.25rem;
    border-bottom: 1px solid #F1F5F9;
    display: flex;
    align-items: center;
    gap: 10px;
    background: #FAFAFA;
}
 
.result-header-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.9rem;
    font-weight: 600;
    color: #0F172A;
}
 
.result-body {
    padding: 1.25rem;
    font-size: 0.875rem;
    color: #374151;
    line-height: 1.6;
    white-space: pre-wrap;
}
 
/* ── Permission toggles ── */
.stCheckbox > label,
.stCheckbox > label > div,
.stCheckbox > label p,
.stCheckbox span:not([data-testid]),
[data-testid="stCheckbox"] label,
[data-testid="stCheckbox"] p,
[data-testid="stCheckbox"] span {
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: #374151 !important;
}
 
/* Fix all main content text being overridden by sidebar */
.main .stCheckbox label,
.main .stCheckbox span,
.main .stRadio label,
.main .stRadio span,
.main label,
section[data-testid="stSidebar"] ~ div label,
section[data-testid="stSidebar"] ~ div .stCheckbox span,
section[data-testid="stSidebar"] ~ div .stRadio span {
    color: #374151 !important;
}
 
/* Nuclear option - force dark text everywhere outside sidebar */
div[data-testid="stVerticalBlock"] .stCheckbox label,
div[data-testid="stVerticalBlock"] .stCheckbox p,
div[data-testid="stVerticalBlock"] .stCheckbox span,
div[data-testid="stHorizontalBlock"] .stCheckbox label,
div[data-testid="stHorizontalBlock"] .stCheckbox p,
div[data-testid="stHorizontalBlock"] .stCheckbox span {
    color: #374151 !important;
}
 
/* ── Security badge ── */
.security-active {
    background: #F0FDF4;
    border: 1px solid #BBF7D0;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 0.8rem;
    color: #15803D;
    font-family: 'Inter', monospace;
    margin: 1rem 0;
}
 
/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #F1F5F9;
    border-radius: 12px;
    padding: 4px;
    border: none;
}
 
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: #64748B !important;
    padding: 8px 16px !important;
    border: none !important;
    background: transparent !important;
}
 
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #0F172A !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
    font-weight: 600 !important;
}
 
/* ── File uploader ── */
[data-testid="stFileUploader"] {
    border: 2px dashed #E2E8F0 !important;
    border-radius: 12px !important;
    background: #FAFAFA !important;
}
 
/* ── Radio ── */
.stRadio > div {
    gap: 8px;
}

.stRadio label,
.stRadio label p,
.stRadio label span,
.stRadio div[role="radiogroup"] label,
.stRadio div[data-testid="stMarkdownContainer"] p,
[data-testid="stRadio"] label,
[data-testid="stRadio"] span,
[data-testid="stRadio"] p {
    color: #374151 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}
 
/* ── Divider ── */
hr {
    border: none;
    border-top: 1px solid #F1F5F9;
    margin: 1.5rem 0;
}
 
/* ── Success/Error/Info ── */
.stSuccess, .stInfo, .stWarning, .stError {
    border-radius: 10px !important;
    font-size: 0.85rem !important;
}
 
/* ── Expander ── */
.streamlit-expanderHeader {
    background: #F8FAFC !important;
    border-radius: 10px !important;
    font-size: 0.875rem !important;
    font-weight: 600 !important;
}
 
</style>
""", unsafe_allow_html=True)
 
# ── Helper Functions ──────────────────────────────────────────────────────────
async def run_agent_async(agent, app_name, user_id, session_id, message, retries=3):
    ss = InMemorySessionService()
    await ss.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    runner = Runner(agent=agent, app_name=app_name, session_service=ss)
 
    for attempt in range(retries):
        try:
            response_text = ""
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=types.Content(
                    role="user",
                    parts=[types.Part(text=message)]
                ),
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            response_text += part.text
            return response_text
        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "429" in error_msg or "UNAVAILABLE" in error_msg:
                wait = (attempt + 1) * 10
                await asyncio.sleep(wait)
            else:
                raise e
    raise Exception("Max retries reached.")
 
 
def run_agent(agent, app_name, user_id, session_id, message):
    return asyncio.run(run_agent_async(agent, app_name, user_id, session_id, message))
 
 
def extract_pdf_text(pdf_file) -> str:
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        return "\n".join(page.extract_text() for page in reader.pages)
    except Exception as e:
        return f"Error reading PDF: {e}"
 
 
# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-logo">🚀 CareerPilot AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tagline">Multi-Agent Career Development</div>', unsafe_allow_html=True)
 
    st.markdown('<div class="sidebar-section">Active Agents</div>', unsafe_allow_html=True)
 
    agents_info = [
        ("Profile Analyzer",   "Strengths, gaps & readiness score"),
        ("Career Planner",     "24-month personalized roadmap"),
        ("Resume Agent",       "ATS score & keyword analysis"),
        ("Project Generator",  "3 tailored portfolio projects"),
        ("Interview Agent",    "Technical & behavioral prep"),
        ("Learning Agent",     "GitHub-sourced study plan"),
    ]
    for name, desc in agents_info:
        st.markdown(f"""
        <div class="agent-item">
            <div class="agent-dot"></div>
            <div>
                <div style="font-weight:500;font-size:0.82rem">{name}</div>
                <div style="font-size:0.72rem;color:#475569;margin-top:1px">{desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
 
    st.markdown('<div class="sidebar-section">Security</div>', unsafe_allow_html=True)
    for item in ["Email & phone masking", "Permission system", "Local data vault", "No external storage"]:
        st.markdown(f'<div class="security-item">🔒 {item}</div>', unsafe_allow_html=True)
 
    st.markdown('<div class="sidebar-section">Built With</div>', unsafe_allow_html=True)
    for item in ["Google ADK", "Gemini 3.5 Flash", "Filesystem MCP", "GitHub MCP", "Streamlit"]:
        st.markdown(f'<div class="security-item">⚡ {item}</div>', unsafe_allow_html=True)
 
# ── Main Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding: 2rem 0 1rem 0;">
    <div style="font-family:'Space Grotesk',sans-serif;font-size:1.75rem;font-weight:700;color:#0F172A;letter-spacing:-0.5px">
        Career Development Report
    </div>
    <div style="font-size:0.875rem;color:#64748B;margin-top:4px">
        Fill in your profile below and let 6 AI agents build your personalized career plan
    </div>
</div>
""", unsafe_allow_html=True)
 
# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["✏️  My Profile", "📊  My Report", "ℹ️  About"])
 
# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PROFILE INPUT
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
 
    # ── Personal Info Card ──
    st.markdown("""
    <div class="card">
        <div class="card-header">
            <div class="card-icon icon-blue">👤</div>
            <div>
                <div class="card-title">Personal Information</div>
                <div class="card-desc">Tell us who you are and where you want to go</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        name = st.text_input("Full Name", placeholder="e.g. Ahmed Al-Rashid")
        current_level = st.selectbox("Current Level", [
            "High School Student",
            "First-year University Student",
            "Second-year University Student",
            "Third-year University Student",
            "Final-year University Student",
            "Recent Graduate",
            "Early Professional (1-2 years)",
        ])
        field_of_study = st.text_input("Field of Study", placeholder="e.g. Computer Science")
 
    with col2:
        career_goal = st.text_input("Career Goal", placeholder="e.g. AI Engineer, Data Scientist")
        skills = st.text_area("Current Skills", placeholder="e.g. Python basics, HTML, some math", height=106)
 
    experience = st.text_area("Experience & Projects", placeholder="e.g. No internships yet. Built a calculator in Python for a university assignment.", height=90)
 
    st.markdown("<hr>", unsafe_allow_html=True)
 
    # ── CV Upload Card ──
    st.markdown("""
    <div class="card-header" style="margin-bottom:1rem">
        <div class="card-icon icon-purple">📄</div>
        <div>
            <div class="card-title">Your CV / Resume</div>
            <div class="card-desc">Upload a PDF or paste your CV text</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    cv_option = st.radio("CV Input Method", ["📎 Upload PDF", "📋 Paste Text", "🧪 Use Sample CV"], horizontal=True, label_visibility="collapsed")
 
    cv_text = ""
    if cv_option == "📎 Upload PDF":
        uploaded = st.file_uploader("Upload your CV (PDF)", type=["pdf"], label_visibility="collapsed")
        if uploaded:
            cv_text = extract_pdf_text(uploaded)
            st.success(f"✅ CV extracted — {len(cv_text.split())} words")
            with st.expander("Preview"):
                st.text(cv_text[:600] + "..." if len(cv_text) > 600 else cv_text)
 
    elif cv_option == "📋 Paste Text":
        cv_text = st.text_area("Paste CV here", height=180, placeholder="Paste your full CV text...", label_visibility="collapsed")
 
    else:
        cv_text = """
        Ahmed Al-Rashid | ahmed@email.com | +966 50 000 0000
        Education: BSc Computer Science — King Abdulaziz University (2024–Present) GPA 3.8
        Skills: Python (beginner), Microsoft Office, HTML basics
        Projects: Calculator in Python (university), simple HTML website (group project)
        Languages: Arabic (native), English (intermediate)
        """
        st.info("🧪 Using sample CV for demonstration")
 
    st.markdown("<hr>", unsafe_allow_html=True)
 
    # ── Permissions & Agent Selection ──
    pcol1, pcol2 = st.columns(2, gap="medium")
 
    with pcol1:
        st.markdown("""
        <div class="card-header" style="margin-bottom:0.75rem">
            <div class="card-icon icon-green">🔒</div>
            <div>
                <div class="card-title">Data Permissions</div>
                <div class="card-desc">Approve before processing</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        perm_profile = st.checkbox("Profile Information", value=True)
        perm_cv      = st.checkbox("CV / Resume", value=True)
        perm_github  = st.checkbox("GitHub Profile (optional)", value=False)
 
    with pcol2:
        st.markdown("""
        <div class="card-header" style="margin-bottom:0.75rem">
            <div class="card-icon icon-orange">🤖</div>
            <div>
                <div class="card-title">Select Agents</div>
                <div class="card-desc">Choose which agents to run</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        run_profile   = st.checkbox("🔍 Profile Analyzer", value=True)
        run_career    = st.checkbox("🗺️ Career Planner", value=True)
        run_resume    = st.checkbox("📄 Resume Agent", value=True)
        run_projects  = st.checkbox("💡 Project Generator", value=True)
        run_interview = st.checkbox("🎤 Interview Agent", value=True)
        run_learning  = st.checkbox("📚 Learning Agent", value=True)
 
    st.markdown("<br>", unsafe_allow_html=True)
 
    generate_btn = st.button("🚀  Generate My Career Report", type="primary", use_container_width=True)
 
# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — REPORT OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    if generate_btn:
 
        # Validation
        if not name or not career_goal:
            st.error("Please fill in your Name and Career Goal before generating.")
            st.stop()
        if not perm_profile or not perm_cv:
            st.error("Profile and CV permissions are required.")
            st.stop()
        if not cv_text:
            st.error("Please provide your CV before generating.")
            st.stop()
 
        user_input = f"""
        My name is {name}. I am a {current_level} studying {field_of_study}.
        My skills: {skills}. Experience: {experience}.
        My career goal is to become a {career_goal}.
        """
 
        # Security
        st.markdown("""
        <div style="font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;color:#0F172A;margin-bottom:1rem">
            🔒 Security Check
        </div>
        """, unsafe_allow_html=True)
 
        masked_cv, cv_vault           = mask_personal_data(cv_text)
        masked_profile, profile_vault = mask_personal_data(user_input)
        vault = {**cv_vault, **profile_vault}
 
        if vault:
            items = " · ".join([f"{k} → {v[:3]}***" for k, v in vault.items()])
            st.markdown(f'<div class="security-active">🛡️ Protected: {items}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="security-active">✅ No sensitive PII detected in your input</div>', unsafe_allow_html=True)
 
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;color:#0F172A;margin-bottom:1rem">
            📊 Your Career Report
        </div>
        """, unsafe_allow_html=True)
 
        app_name = "careerpilot_ai"
        user_id  = "user_001"
 
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
                st.markdown(content)
 
        # Agent 1
        if run_profile:
            with st.spinner("🔍 Analyzing your profile..."):
                try:
                    profile_result = run_agent(profile_analyzer, app_name, user_id, "s001", masked_profile)
                    st.session_state["profile_result"] = profile_result
                    render_result("🔍", "Profile Analysis", profile_result)
                    st.success("Profile analysis complete")
                except Exception as e:
                    st.error(f"Profile analysis failed: {e}")
                    st.stop()
 
        # Agent 2
        if run_career:
            with st.spinner("🗺️ Building your career roadmap..."):
                try:
                    career_result = run_agent(career_planner, app_name, user_id, "s002",
                        f"Profile: {masked_profile}\nAnalysis: {st.session_state.get('profile_result','')}\nCreate roadmap.")
                    st.session_state["career_result"] = career_result
                    render_result("🗺️", "Career Roadmap", career_result)
                    st.success("Career roadmap complete")
                except Exception as e:
                    st.error(f"Career planning failed: {e}")
 
        # Agent 3
        if run_resume:
            with st.spinner("📄 Reviewing your resume..."):
                try:
                    resume_result = run_agent(resume_agent, app_name, user_id, "s003",
                        f"Profile: {masked_profile}\nTarget: {career_goal}\nCV: {masked_cv}\nAnalyze ATS.")
                    render_result("📄", "Resume Analysis", resume_result)
                    st.success("Resume analysis complete")
                except Exception as e:
                    st.error(f"Resume analysis failed: {e}")
 
        # Agent 4
        if run_projects:
            with st.spinner("💡 Generating project ideas..."):
                try:
                    project_result = run_agent(project_generator, app_name, user_id, "s004",
                        f"Profile: {masked_profile}\nAnalysis: {st.session_state.get('profile_result','')}\nSuggest 3 projects for {career_goal}.")
                    render_result("💡", "Project Suggestions", project_result)
                    st.success("Project suggestions complete")
                except Exception as e:
                    st.error(f"Project generation failed: {e}")
 
        # Agent 5
        if run_interview:
            with st.spinner("🎤 Generating interview guide..."):
                try:
                    interview_result = run_agent(interview_agent, app_name, user_id, "s005",
                        f"Profile: {masked_profile}\nAnalysis: {st.session_state.get('profile_result','')}\nTarget: {career_goal}\nGenerate interview guide.")
                    render_result("🎤", "Interview Preparation", interview_result)
                    st.success("Interview guide complete")
                except Exception as e:
                    st.error(f"Interview prep failed: {e}")
 
        # Agent 6
        if run_learning:
            with st.spinner("📚 Building learning plan from GitHub..."):
                try:
                    learning_result = run_agent(learning_agent, app_name, user_id, "s006",
                        f"Profile: {masked_profile}\nSkill gaps: {st.session_state.get('profile_result','')}\nTarget: {career_goal}\nBuild learning plan.")
                    render_result("📚", "Personalized Learning Plan", learning_result)
                    st.success("Learning plan complete")
                except Exception as e:
                    st.error(f"Learning plan failed: {e}")
 
        st.balloons()
        st.markdown("""
        <div style="background:#0F172A;border-radius:16px;padding:1.5rem;text-align:center;margin-top:1rem">
            <div style="font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:600;color:#FFFFFF;margin-bottom:4px">
                🎉 Your CareerPilot Report is Ready
            </div>
            <div style="font-size:0.8rem;color:#94A3B8">
                Save this page or screenshot your results
            </div>
        </div>
        """, unsafe_allow_html=True)
 
    else:
        # Empty state
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem">
            <div style="font-size:3rem;margin-bottom:1rem">🚀</div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:1.25rem;font-weight:600;color:#0F172A;margin-bottom:8px">
                Your report will appear here
            </div>
            <div style="font-size:0.875rem;color:#64748B;max-width:400px;margin:0 auto">
                Fill in your profile in the <strong>My Profile</strong> tab and click Generate to get your personalized career development report.
            </div>
        </div>
 
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;max-width:700px;margin:2rem auto">
            <div class="card" style="text-align:center;padding:1.25rem">
                <div style="font-size:1.5rem;margin-bottom:8px">🔍</div>
                <div style="font-size:0.8rem;font-weight:600;color:#0F172A">Profile Analysis</div>
                <div style="font-size:0.75rem;color:#64748B;margin-top:4px">Readiness score & skill gaps</div>
            </div>
            <div class="card" style="text-align:center;padding:1.25rem">
                <div style="font-size:1.5rem;margin-bottom:8px">🗺️</div>
                <div style="font-size:0.8rem;font-weight:600;color:#0F172A">Career Roadmap</div>
                <div style="font-size:0.75rem;color:#64748B;margin-top:4px">24-month action plan</div>
            </div>
            <div class="card" style="text-align:center;padding:1.25rem">
                <div style="font-size:1.5rem;margin-bottom:8px">📄</div>
                <div style="font-size:0.8rem;font-weight:600;color:#0F172A">Resume Review</div>
                <div style="font-size:0.75rem;color:#64748B;margin-top:4px">ATS score & improvements</div>
            </div>
            <div class="card" style="text-align:center;padding:1.25rem">
                <div style="font-size:1.5rem;margin-bottom:8px">💡</div>
                <div style="font-size:0.8rem;font-weight:600;color:#0F172A">Project Ideas</div>
                <div style="font-size:0.75rem;color:#64748B;margin-top:4px">3 tailored portfolio projects</div>
            </div>
            <div class="card" style="text-align:center;padding:1.25rem">
                <div style="font-size:1.5rem;margin-bottom:8px">🎤</div>
                <div style="font-size:0.8rem;font-weight:600;color:#0F172A">Interview Prep</div>
                <div style="font-size:0.75rem;color:#64748B;margin-top:4px">12 tailored questions</div>
            </div>
            <div class="card" style="text-align:center;padding:1.25rem">
                <div style="font-size:1.5rem;margin-bottom:8px">📚</div>
                <div style="font-size:0.8rem;font-weight:600;color:#0F172A">Learning Plan</div>
                <div style="font-size:0.75rem;color:#64748B;margin-top:4px">Real GitHub resources</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
 
# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ABOUT
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("""
    <div class="card">
        <div class="card-header">
            <div class="card-icon icon-blue">🚀</div>
            <div>
                <div class="card-title">About CareerPilot AI</div>
                <div class="card-desc">Multi-Agent Career Development Platform</div>
            </div>
        </div>
        <div style="font-size:0.875rem;color:#374151;line-height:1.7">
            CareerPilot AI is a multi-agent system built with Google's Agent Development Kit (ADK)
            that helps students and early professionals navigate their career journey.
            <br><br>
            The system uses 6 specialized AI agents working in sequence, two MCP servers for
            real-world data integration, and a security layer that protects personal information
            before any data is processed.
            <br><br>
            Built for the <strong>Kaggle 5-Day AI Agents Capstone Project</strong> — Agents for Good track.
        </div>
    </div>
 
    <div class="card">
        <div class="card-header">
            <div class="card-icon icon-purple">🏗️</div>
            <div>
                <div class="card-title">Architecture</div>
                <div class="card-desc">How the system works</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
 
    st.code("""
User Input (Profile + CV)
        ↓
🔒 Security Layer  →  PII masking · Permission system · Data vault
        ↓
📂 Filesystem MCP  →  Read CV from disk · Save report
🐙 GitHub MCP      →  Search real learning repositories
        ↓
🤖 Agent Pipeline (Google ADK)
   Agent 1: Profile Analyzer   →  Strengths, gaps, readiness score
   Agent 2: Career Planner     →  4-phase 24-month roadmap
   Agent 3: Resume Agent       →  ATS score & improvements
   Agent 4: Project Generator  →  3 tailored portfolio projects
   Agent 5: Interview Agent    →  Technical & behavioral questions
   Agent 6: Learning Agent     →  GitHub-sourced study plan
        ↓
📊 Full Report  →  Saved to outputs/ via Filesystem MCP
    """, language="text")
 
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="card" style="text-align:center">
            <div style="font-size:1.75rem;font-weight:700;color:#0F172A;font-family:'Space Grotesk',sans-serif">6</div>
            <div style="font-size:0.8rem;color:#64748B;margin-top:4px">AI Agents</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="card" style="text-align:center">
            <div style="font-size:1.75rem;font-weight:700;color:#0F172A;font-family:'Space Grotesk',sans-serif">2</div>
            <div style="font-size:0.8rem;color:#64748B;margin-top:4px">MCP Servers</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="card" style="text-align:center">
            <div style="font-size:1.75rem;font-weight:700;color:#0F172A;font-family:'Space Grotesk',sans-serif">3</div>
            <div style="font-size:0.8rem;color:#64748B;margin-top:4px">Security Layers</div>
        </div>
        """, unsafe_allow_html=True)