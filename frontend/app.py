import streamlit as st
import asyncio
import sys
import os

# Add parent directory to path so we can import agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agents.profile_analyzer import profile_analyzer
from agents.career_planner import career_planner
from agents.resume_agent import resume_agent
from agents.project_generator import project_generator
from agents.interview_agent import interview_agent
from tools.security import mask_personal_data, get_security_report
import PyPDF2
import io

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CareerPilot AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
    }
    .agent-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .security-badge {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        color: #155724;
        font-size: 0.9rem;
    }
    .step-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #667eea;
        margin: 1rem 0 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Helper: Run agent ─────────────────────────────────────────────────────────
async def run_agent_async(agent, app_name, user_id, session_id, message, retries=3):
    """Run a single agent and return response text."""
    ss = InMemorySessionService()
    await ss.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
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
                st.warning(f"⏳ Server busy. Retrying in {wait}s... (attempt {attempt+1}/{retries})")
                await asyncio.sleep(wait)
            else:
                st.error(f"❌ Agent error: {error_msg}")
                raise e

    raise Exception("Max retries reached.")


def run_agent(agent, app_name, user_id, session_id, message):
    """Sync wrapper for async agent runner."""
    return asyncio.run(run_agent_async(agent, app_name, user_id, session_id, message))


def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from uploaded PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🚀 CareerPilot AI</h1>
    <p>Multi-Agent Career Development Platform</p>
    <p><small>Powered by Google ADK + Gemini</small></p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/rocket.png", width=80)
    st.title("CareerPilot AI")
    st.markdown("---")

    st.markdown("### 🤖 Active Agents")
    agents_list = [
        ("🔍", "Profile Analyzer"),
        ("🗺️", "Career Planner"),
        ("📄", "Resume Agent"),
        ("💡", "Project Generator"),
        ("🎤", "Interview Agent"),
    ]
    for icon, name in agents_list:
        st.markdown(f"{icon} {name}")

    st.markdown("---")
    st.markdown("### 🔒 Security Features")
    st.markdown("✅ Email masking")
    st.markdown("✅ Phone masking")
    st.markdown("✅ Permission layer")
    st.markdown("✅ Data vault")

    st.markdown("---")
    st.markdown("### 📋 How It Works")
    st.markdown("1. Fill in your profile")
    st.markdown("2. Upload your CV")
    st.markdown("3. Grant permissions")
    st.markdown("4. Get your full report")

# ── Main Content ──────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📝 My Profile", "📊 My Report", "ℹ️ About"])

# ── TAB 1: Profile Input ──────────────────────────────────────────────────────
with tab1:
    st.markdown("## Tell Us About Yourself")
    st.markdown("Fill in your details below to generate your personalized career report.")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("👤 Your Name", placeholder="e.g. Ahmed Al-Rashid")
        current_level = st.selectbox(
            "📚 Current Level",
            [
                "High School Student",
                "First-year University Student",
                "Second-year University Student",
                "Third-year University Student",
                "Final-year University Student",
                "Recent Graduate",
                "Early Professional (1-2 years)",
            ]
        )
        field_of_study = st.text_input(
            "🎓 Field of Study",
            placeholder="e.g. Computer Science"
        )

    with col2:
        career_goal = st.text_input(
            "🎯 Career Goal",
            placeholder="e.g. AI Engineer, Data Scientist"
        )
        skills = st.text_area(
            "💻 Current Skills",
            placeholder="e.g. Python basics, HTML, some math",
            height=100,
        )
        experience = st.text_area(
            "💼 Experience / Projects",
            placeholder="e.g. No internships yet. Built a calculator in Python.",
            height=100,
        )

    st.markdown("---")
    st.markdown("### 📄 Upload Your CV")

    cv_option = st.radio(
        "How would you like to provide your CV?",
        ["Upload PDF", "Paste as Text", "Use Sample CV"],
        horizontal=True,
    )

    cv_text = ""

    if cv_option == "Upload PDF":
        uploaded_file = st.file_uploader(
            "Upload your CV (PDF)", type=["pdf"]
        )
        if uploaded_file:
            cv_text = extract_text_from_pdf(uploaded_file)
            st.success("✅ CV uploaded and extracted successfully!")
            with st.expander("Preview extracted text"):
                st.text(cv_text[:500] + "..." if len(cv_text) > 500 else cv_text)

    elif cv_option == "Paste as Text":
        cv_text = st.text_area(
            "Paste your CV content here",
            height=200,
            placeholder="Paste your full CV text here..."
        )

    else:
        cv_text = """
        Ahmed Al-Rashid
        Email: ahmed@email.com | Phone: +966 50 000 0000
        EDUCATION: Bachelor of Computer Science — 2024-Present, GPA 3.8
        SKILLS: Python (beginner), Microsoft Office, HTML basics
        PROJECTS: Calculator in Python, simple HTML website
        LANGUAGES: Arabic (native), English (intermediate)
        """
        st.info("Using sample CV for demonstration.")

    st.markdown("---")
    st.markdown("### 🔒 Data Permissions")
    st.markdown("CareerPilot protects your data. Please grant access below:")

    perm_col1, perm_col2, perm_col3 = st.columns(3)
    with perm_col1:
        perm_profile = st.checkbox("✅ Profile Information", value=True)
    with perm_col2:
        perm_cv = st.checkbox("✅ CV / Resume", value=True)
    with perm_col3:
        perm_github = st.checkbox("GitHub Profile (optional)", value=False)

    st.markdown("---")

    # Select which agents to run
    st.markdown("### 🤖 Select Agents to Run")
    agent_col1, agent_col2, agent_col3, agent_col4, agent_col5 = st.columns(5)
    with agent_col1:
        run_profile  = st.checkbox("🔍 Profile", value=True)
    with agent_col2:
        run_career   = st.checkbox("🗺️ Career", value=True)
    with agent_col3:
        run_resume   = st.checkbox("📄 Resume", value=True)
    with agent_col4:
        run_projects = st.checkbox("💡 Projects", value=True)
    with agent_col5:
        run_interview = st.checkbox("🎤 Interview", value=True)

    st.markdown("---")

    # Generate button
    generate_btn = st.button(
        "🚀 Generate My Career Report",
        type="primary",
        use_container_width=True,
    )

# ── TAB 2: Report Output ──────────────────────────────────────────────────────
with tab2:
    if generate_btn:
        # Validation
        if not name or not career_goal:
            st.error("❌ Please fill in your Name and Career Goal before generating.")
            st.stop()

        if not perm_profile or not perm_cv:
            st.error("❌ Profile and CV permissions are required to proceed.")
            st.stop()

        if not cv_text:
            st.error("❌ Please provide your CV before generating.")
            st.stop()

        # Build profile text
        user_input = f"""
        My name is {name}.
        I am a {current_level} studying {field_of_study}.
        My skills include: {skills}.
        Experience and projects: {experience}.
        My career goal is to become a {career_goal}.
        """

        # Security masking
        st.markdown("### 🔒 Security Layer")
        masked_cv, cv_vault          = mask_personal_data(cv_text)
        masked_profile, profile_vault = mask_personal_data(user_input)
        vault = {**cv_vault, **profile_vault}

        if vault:
            st.markdown(
                f'<div class="security-badge">{get_security_report(vault)}</div>',
                unsafe_allow_html=True
            )
        else:
            st.success("✅ No sensitive personal data detected.")

        app_name = "careerpilot_ai"
        user_id  = "user_001"

        st.markdown("---")
        st.markdown("## 📊 Your CareerPilot Report")

        # ── Agent 1: Profile Analysis ──
        if run_profile:
            st.markdown('<div class="step-header">🔍 Step 1: Profile Analysis</div>',
                        unsafe_allow_html=True)
            with st.spinner("Analyzing your profile..."):
                try:
                    profile_result = run_agent(
                        profile_analyzer, app_name, user_id,
                        "session_001", masked_profile
                    )
                    st.session_state["profile_result"] = profile_result
                    with st.expander("View Profile Analysis", expanded=True):
                        st.markdown(profile_result)
                    st.success("✅ Profile analysis complete!")
                except Exception as e:
                    st.error(f"Profile analysis failed: {str(e)}")
                    st.stop()

        # ── Agent 2: Career Planner ──
        if run_career:
            st.markdown('<div class="step-header">🗺️ Step 2: Career Roadmap</div>',
                        unsafe_allow_html=True)
            with st.spinner("Building your career roadmap..."):
                try:
                    career_input = f"""
User Profile: {masked_profile}
Profile Analysis: {st.session_state.get('profile_result', '')}
Create a detailed career roadmap.
"""
                    career_result = run_agent(
                        career_planner, app_name, user_id,
                        "session_002", career_input
                    )
                    st.session_state["career_result"] = career_result
                    with st.expander("View Career Roadmap", expanded=True):
                        st.markdown(career_result)
                    st.success("✅ Career roadmap complete!")
                except Exception as e:
                    st.error(f"Career planning failed: {str(e)}")

        # ── Agent 3: Resume Review ──
        if run_resume:
            st.markdown('<div class="step-header">📄 Step 3: Resume Analysis</div>',
                        unsafe_allow_html=True)
            with st.spinner("Reviewing your resume..."):
                try:
                    resume_input = f"""
User Profile: {masked_profile}
Target Role: {career_goal}
CV Content: {masked_cv}
Analyze for ATS compatibility.
"""
                    resume_result = run_agent(
                        resume_agent, app_name, user_id,
                        "session_003", resume_input
                    )
                    st.session_state["resume_result"] = resume_result
                    with st.expander("View Resume Analysis", expanded=True):
                        st.markdown(resume_result)
                    st.success("✅ Resume analysis complete!")
                except Exception as e:
                    st.error(f"Resume analysis failed: {str(e)}")

        # ── Agent 4: Project Generator ──
        if run_projects:
            st.markdown('<div class="step-header">💡 Step 4: Project Suggestions</div>',
                        unsafe_allow_html=True)
            with st.spinner("Generating project ideas..."):
                try:
                    project_input = f"""
User Profile: {masked_profile}
Profile Analysis: {st.session_state.get('profile_result', '')}
Suggest 3 projects to bridge skill gaps for {career_goal} role.
"""
                    project_result = run_agent(
                        project_generator, app_name, user_id,
                        "session_004", project_input
                    )
                    st.session_state["project_result"] = project_result
                    with st.expander("View Project Suggestions", expanded=True):
                        st.markdown(project_result)
                    st.success("✅ Project suggestions complete!")
                except Exception as e:
                    st.error(f"Project generation failed: {str(e)}")

        # ── Agent 5: Interview Agent ──
        if run_interview:
            st.markdown('<div class="step-header">🎤 Step 5: Interview Preparation</div>',
                        unsafe_allow_html=True)
            with st.spinner("Generating interview questions..."):
                try:
                    interview_input = f"""
User Profile: {masked_profile}
Profile Analysis: {st.session_state.get('profile_result', '')}
Target Role: {career_goal}
Generate personalized interview preparation guide.
"""
                    interview_result = run_agent(
                        interview_agent, app_name, user_id,
                        "session_005", interview_input
                    )
                    with st.expander("View Interview Guide", expanded=True):
                        st.markdown(interview_result)
                    st.success("✅ Interview guide complete!")
                except Exception as e:
                    st.error(f"Interview prep failed: {str(e)}")

        st.markdown("---")
        st.balloons()
        st.success("🎉 Your full CareerPilot AI report is ready!")

    else:
        st.info("👈 Fill in your profile in the **My Profile** tab and click **Generate My Career Report**.")
        st.markdown("""
        ### What you'll get:
        - 🔍 **Profile Analysis** — strengths, weaknesses, skill gaps, readiness score
        - 🗺️ **Career Roadmap** — 4-phase plan over 24 months
        - 📄 **Resume Analysis** — ATS score and specific improvements
        - 💡 **Project Suggestions** — 3 tailored projects to build
        - 🎤 **Interview Guide** — technical, coding, and behavioral questions
        """)

# ── TAB 3: About ──────────────────────────────────────────────────────────────
with tab3:
    st.markdown("## About CareerPilot AI")
    st.markdown("""
    CareerPilot AI is a multi-agent career development platform built with:

    - **Google Agent Development Kit (ADK)** — multi-agent orchestration
    - **Gemini** — AI model powering all agents
    - **MCP Servers** — filesystem integration for CV reading
    - **Streamlit** — interactive web frontend
    - **Security Layer** — personal data masking and permission system

    ### Architecture
                User Input
    ↓
Security Layer (mask PII)
    ↓
Orchestrator
    ↓
┌─────────────────────────────────────┐
│  Profile   Career   Resume  Project  Interview  │
│  Analyzer  Planner  Agent   Gen      Agent      │
└─────────────────────────────────────┘
    ↓
Full Career Report
                ### Built for
    Kaggle 5-Day AI Agents Capstone Project
    Track: Agents for Good
    """)