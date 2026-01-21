import os
import requests
from pathlib import Path

# Load .env only if file exists (for local development)
if Path(".env").exists():
    from dotenv import load_dotenv
    load_dotenv()


def create_github_issue(username: str, email: str, title: str, description: str) -> str:
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")

    if not token or not repo:
        return "Error: GITHUB_TOKEN or GITHUB_REPO not configured"

    body = f"""**User Request:**
- **Name:** {username}
- **Email:** {email}

---

**Description:**

{description}
"""

    payload = {
        "title": title,
        "body": body,
        "labels": ["support", "user-request"]
    }

    try:
        response = requests.post(
            f"https://api.github.com/repos/{repo}/issues",
            json=payload,
            headers={
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            },
            timeout=10
        )

        if response.status_code == 201:
            data = response.json()
            return f"✅ Issue #{data['number']} created\n🔗 {data['html_url']}"
        else:
            return f"❌ Failed to create issue: {response.status_code}"

    except requests.RequestException as e:
        return f"❌ Error: {str(e)}"
