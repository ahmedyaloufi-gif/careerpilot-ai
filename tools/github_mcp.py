import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ── GitHub MCP Tool ──────────────────────────────────────────────────────────

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

def search_github_repositories(query: str, max_results: int = 5) -> dict:
    """
    MCP-style tool: searches GitHub for repositories matching a query.
    Used by Learning Agent to find real learning resources.
    """
    try:
        url = "https://api.github.com/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": max_results,
        }

        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        repos = []
        for item in data.get("items", []):
            repos.append({
                "name": item["full_name"],
                "description": item.get("description", "No description"),
                "url": item["html_url"],
                "stars": item["stargazers_count"],
                "language": item.get("language", "Unknown"),
                "topics": item.get("topics", []),
            })

        return {
            "success": True,
            "query": query,
            "total_found": data.get("total_count", 0),
            "repositories": repos,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "repositories": [],
        }


def search_learning_resources(skill: str, level: str = "beginner") -> dict:
    """
    MCP-style tool: finds learning resources on GitHub for a specific skill.
    Returns curated repos, roadmaps, and tutorials.
    """
    queries = [
        f"{skill} {level} tutorial",
        f"awesome {skill}",
        f"{skill} roadmap",
        f"learn {skill} projects",
    ]

    all_resources = []
    for query in queries:
        result = search_github_repositories(query, max_results=2)
        if result["success"]:
            all_resources.extend(result["repositories"])

    # Deduplicate by URL
    seen = set()
    unique_resources = []
    for r in all_resources:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique_resources.append(r)

    # Sort by stars
    unique_resources.sort(key=lambda x: x["stars"], reverse=True)

    return {
        "success": True,
        "skill": skill,
        "level": level,
        "resources": unique_resources[:8],
    }


def get_github_user_repos(username: str) -> dict:
    """
    MCP-style tool: fetches a user's public GitHub repositories.
    Used to analyze the user's existing GitHub portfolio.
    """
    try:
        url = f"https://api.github.com/users/{username}/repos"
        params = {
            "sort": "updated",
            "per_page": 10,
        }

        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        repos = []
        for item in data:
            repos.append({
                "name": item["name"],
                "description": item.get("description", "No description"),
                "url": item["html_url"],
                "language": item.get("language", "Unknown"),
                "stars": item["stargazers_count"],
                "updated": item["updated_at"][:10],
            })

        return {
            "success": True,
            "username": username,
            "repo_count": len(repos),
            "repositories": repos,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "repositories": [],
        }


def get_github_mcp_info() -> dict:
    """
    Returns info about the GitHub MCP server.
    """
    return {
        "server_name": "CareerPilot GitHub MCP",
        "version": "1.0.0",
        "tools": [
            {
                "name": "search_github_repositories",
                "description": "Search GitHub for repositories by query",
                "input": "query: str, max_results: int",
                "output": "list of repositories with stars and URLs",
            },
            {
                "name": "search_learning_resources",
                "description": "Find learning resources for a specific skill",
                "input": "skill: str, level: str",
                "output": "curated list of tutorials and roadmaps",
            },
            {
                "name": "get_github_user_repos",
                "description": "Fetch a user's public GitHub repositories",
                "input": "username: str",
                "output": "list of user repositories",
            },
        ],
        "data_source": "GitHub REST API v3",
        "authentication": "Bearer token",
    }