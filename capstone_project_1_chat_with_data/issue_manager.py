import os

import requests


class GitHubIssueError(RuntimeError):
    pass


def _get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise GitHubIssueError(f"Environment variable {name} is required.")
    return value


def create_github_issue(title: str, body: str, labels: list[str] | None = None) -> dict:
    token = _get_env("GITHUB_TOKEN")
    repository = _get_env("GITHUB_REPO")
    api_url = os.getenv("GITHUB_API_URL", "https://api.github.com")
    url = f"{api_url}/repos/{repository}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "steam-llm-agent",
    }
    payload: dict[str, object] = {"title": title, "body": body}
    if labels:
        payload["labels"] = list(labels)

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
    except requests.RequestException as error:
        raise GitHubIssueError(f"Failed to reach GitHub API: {error}") from error

    if response.status_code >= 400:
        detail = response.text
        raise GitHubIssueError(f"GitHub API returned status {response.status_code}: {detail}")

    return response.json()

