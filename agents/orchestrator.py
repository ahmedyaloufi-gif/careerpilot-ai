import os
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

load_dotenv()

# ── Import sub-agents ────────────────────────────────────────────────────────
from agents.profile_analyzer import profile_analyzer
from agents.career_planner import career_planner

# ── Orchestrator Agent ───────────────────────────────────────────────────────
orchestrator = Agent(
    name="CareerPilot_Orchestrator",
    model="gemini-2.5-flash-lite",
    description="Main orchestrator for CareerPilot AI.",
    instruction="""
    You are the CareerPilot AI Orchestrator.

    When a user provides their profile, you MUST complete ALL steps below
    in order without stopping early:

    STEP 1: Greet the user warmly by name and acknowledge their goal.

    STEP 2: Say "🔍 Analyzing your profile..." then transfer to
            Profile_Analyzer and wait for the full analysis.

    STEP 3: After Profile_Analyzer finishes, IMMEDIATELY say
            "🗺️ Building your career roadmap..." then transfer to
            Career_Planner with the same user profile information.

    STEP 4: After Career_Planner finishes, say:
            "✅ Your CareerPilot report is complete! 
            Next up: personalized project suggestions."

    You MUST run BOTH Profile_Analyzer AND Career_Planner every single time.
    Do NOT stop after just one agent.
    """,
    sub_agents=[profile_analyzer, career_planner],
)

# ── Session & Runner Setup ───────────────────────────────────────────────────
session_service = InMemorySessionService()

runner = Runner(
    agent=orchestrator,
    app_name="careerpilot_ai",
    session_service=session_service,
)