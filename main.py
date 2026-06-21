import asyncio
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
from tools.permissions import request_permissions, check_permission
from tools.filesystem_mcp import (
    read_cv_from_file,
    save_report_to_file,
    list_uploaded_files,
    get_mcp_server_info,
)
from tools.github_mcp import (
    search_learning_resources,
    get_github_mcp_info,
)

async def run_agent(runner, session_service, app_name, user_id, session_id, message, retries=3):
    """Run a single agent with retry logic."""
    for attempt in range(retries):
        try:
            await session_service.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
            )
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
            if "503" in error_msg or "UNAVAILABLE" in error_msg:
                wait = (attempt + 1) * 10
                print(f"⏳ Server busy. Retrying in {wait}s... (attempt {attempt+1}/{retries})")
                await asyncio.sleep(wait)
            elif "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                wait = (attempt + 1) * 15
                print(f"⏳ Rate limit hit. Retrying in {wait}s... (attempt {attempt+1}/{retries})")
                await asyncio.sleep(wait)
            else:
                print(f"❌ Error: {error_msg}")
                raise e

    raise Exception("Max retries reached. Please try again later.")


async def run_careerpilot(user_input: str, cv_source: str = None):
    """Run CareerPilot AI - full pipeline with dual MCP servers."""

    app_name = "careerpilot_ai"
    user_id  = "user_001"

    print("\n" + "=" * 50)
    print("🚀  CAREERPILOT AI — CAREER DEVELOPMENT REPORT")
    print("=" * 50)

    # ── MCP Server 1: Filesystem ──────────────────────
    print("\n🔌 MCP Server 1: Filesystem")
    mcp_info = get_mcp_server_info()
    print(f"   ✅ {mcp_info['server_name']} v{mcp_info['version']}")
    print(f"   Tools: {len(mcp_info['tools'])} available")

    # ── MCP Server 2: GitHub ──────────────────────────
    print("\n🔌 MCP Server 2: GitHub")
    github_info = get_github_mcp_info()
    print(f"   ✅ {github_info['server_name']} v{github_info['version']}")
    print(f"   Tools: {len(github_info['tools'])} available")

    # ── MCP: List CV files ────────────────────────────
    print("\n📂 Checking uploads folder...")
    files_result = list_uploaded_files("uploads")
    print(f"   {files_result['message']}")

    # ── MCP: Read CV ──────────────────────────────────
    cv_text = ""
    if cv_source and cv_source.endswith((".pdf", ".txt", ".md")):
        print(f"\n📄 Reading CV via Filesystem MCP: {cv_source}")
        cv_result = read_cv_from_file(cv_source)
        if cv_result["success"]:
            cv_text = cv_result["content"]
            meta    = cv_result["metadata"]
            print(f"   ✅ {meta['file_name']} | {meta['file_size_kb']}KB | {meta['word_count']} words")
        else:
            print(f"   ❌ {cv_result['error']} — using sample CV")
            cv_text = _sample_cv()
    else:
        print("\n📄 No CV path provided — using sample CV.")
        cv_text = _sample_cv()

    # ── SECURITY: Permissions ─────────────────────────
    permissions = request_permissions([
        "CV / Resume",
        "Profile Information",
        "GitHub Profile (optional)",
    ])

    if not check_permission(permissions, "CV / Resume"):
        print("\n❌ CV access denied.")
        return
    if not check_permission(permissions, "Profile Information"):
        print("\n❌ Profile access denied.")
        return

    # ── SECURITY: Mask PII ────────────────────────────
    print("\n🔒 Securing personal data...")
    masked_cv, cv_vault           = mask_personal_data(cv_text)
    masked_profile, profile_vault = mask_personal_data(user_input)
    vault = {**cv_vault, **profile_vault}
    print(get_security_report(vault))

    # ── MCP: Fetch GitHub resources ───────────────────
    print("\n🐙 Fetching learning resources via GitHub MCP...")
    skill_gaps = ["machine learning python", "deep learning beginner", "data science"]
    github_resources = []
    for skill in skill_gaps:
        result = search_learning_resources(skill, "beginner")
        if result["success"]:
            github_resources.extend(result["resources"][:2])
            print(f"   ✅ Found resources for: {skill}")

    # Format resources for agents
    github_context = "\n".join([
        f"- {r['name']} ({r['stars']}⭐): {r['description']} — {r['url']}"
        for r in github_resources[:8]
    ])

    # ── Setup runners ─────────────────────────────────
    ss1 = InMemorySessionService()
    ss2 = InMemorySessionService()
    ss3 = InMemorySessionService()
    ss4 = InMemorySessionService()
    ss5 = InMemorySessionService()
    ss6 = InMemorySessionService()

    runner1 = Runner(agent=profile_analyzer,  app_name=app_name, session_service=ss1)
    runner2 = Runner(agent=career_planner,    app_name=app_name, session_service=ss2)
    runner3 = Runner(agent=resume_agent,      app_name=app_name, session_service=ss3)
    runner4 = Runner(agent=project_generator, app_name=app_name, session_service=ss4)
    runner5 = Runner(agent=interview_agent,   app_name=app_name, session_service=ss5)
    runner6 = Runner(agent=learning_agent,    app_name=app_name, session_service=ss6)

    full_report = "# CAREERPILOT AI REPORT\n\n"

    # ── STEP 1: Profile Analysis ──────────────────────
    print("\n🔍 Step 1: Analyzing profile...\n")
    profile_result = await run_agent(
        runner1, ss1, app_name, user_id, "session_001", masked_profile
    )
    print(profile_result)
    full_report += "## PROFILE ANALYSIS\n" + profile_result + "\n\n"
    await asyncio.sleep(5)

    # ── STEP 2: Career Planning ───────────────────────
    print("🗺️  Step 2: Career roadmap...\n")
    career_result = await run_agent(
        runner2, ss2, app_name, user_id, "session_002",
        f"User Profile: {masked_profile}\nAnalysis: {profile_result}\nCreate roadmap."
    )
    print(career_result)
    full_report += "## CAREER ROADMAP\n" + career_result + "\n\n"
    await asyncio.sleep(5)

    # ── STEP 3: Resume Review ─────────────────────────
    print("📄 Step 3: Resume review...\n")
    resume_result = await run_agent(
        runner3, ss3, app_name, user_id, "session_003",
        f"Profile: {masked_profile}\nTarget: AI Engineer\nCV: {masked_cv}\nAnalyze ATS."
    )
    print(resume_result)
    full_report += "## RESUME ANALYSIS\n" + resume_result + "\n\n"
    await asyncio.sleep(5)

    # ── STEP 4: Project Generator ─────────────────────
    print("💡 Step 4: Project ideas...\n")
    project_result = await run_agent(
        runner4, ss4, app_name, user_id, "session_004",
        f"Profile: {masked_profile}\nAnalysis: {profile_result}\nSuggest 3 projects."
    )
    print(project_result)
    full_report += "## PROJECT SUGGESTIONS\n" + project_result + "\n\n"
    await asyncio.sleep(5)

    # ── STEP 5: Interview Prep ────────────────────────
    print("🎤 Step 5: Interview guide...\n")
    interview_result = await run_agent(
        runner5, ss5, app_name, user_id, "session_005",
        f"Profile: {masked_profile}\nAnalysis: {profile_result}\nTarget: AI Engineer\nGenerate interview guide."
    )
    print(interview_result)
    full_report += "## INTERVIEW GUIDE\n" + interview_result + "\n\n"
    await asyncio.sleep(5)

    # ── STEP 6: Learning Plan (with GitHub MCP data) ──
    print("📚 Step 6: Personalized learning plan...\n")
    learning_result = await run_agent(
        runner6, ss6, app_name, user_id, "session_006",
        f"""
Profile: {masked_profile}
Skill Gaps: {profile_result}
Target Role: AI Engineer

GitHub Resources found via MCP:
{github_context}

Build a personalized learning plan using these real resources.
"""
    )
    print(learning_result)
    full_report += "## LEARNING PLAN\n" + learning_result + "\n\n"

    # ── MCP: Save report to disk ──────────────────────
    print("\n💾 Saving report via Filesystem MCP...")
    save_result = save_report_to_file(full_report, "outputs/careerpilot_report.txt")
    if save_result["success"]:
        print(f"   ✅ {save_result['message']} ({save_result['file_size_kb']} KB)")

    print("\n" + "=" * 50)
    print("✅  Full CareerPilot Report Complete!")
    print("=" * 50 + "\n")


def _sample_cv() -> str:
    return """
    Ahmed Al-Rashid
    Email: ahmed@email.com | Phone: +966 50 000 0000
    EDUCATION: Bachelor CS — King Abdulaziz University 2024-Present, GPA 3.8
    SKILLS: Python (beginner), Microsoft Office, HTML basics
    PROJECTS: Calculator in Python, simple HTML website
    LANGUAGES: Arabic (native), English (intermediate)
    """


if __name__ == "__main__":
    user_input = """
    My name is Ahmed. I am a first-year Computer Science student.
    I know Python basics and some math. I want to become an AI Engineer.
    I have no internships or deployed projects yet.
    """
    asyncio.run(run_careerpilot(user_input, cv_source=None))