"""Thin wrapper around the public GitHub REST API — unauthenticated, so it
works out of the box but is subject to GitHub's low unauthenticated rate
limit (60 requests/hour per IP). Set GITHUB_TOKEN in the environment and
pass it through here if you need more headroom.
"""

import os

import requests

from app.modules.coding_assistant.schemas import GithubRepoInfo

_API_BASE = "https://api.github.com"


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def get_repo_info(owner: str, repo: str) -> GithubRepoInfo:
    resp = requests.get(f"{_API_BASE}/repos/{owner}/{repo}", headers=_headers(), timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return GithubRepoInfo(
        full_name=data["full_name"],
        description=data.get("description"),
        stars=data.get("stargazers_count", 0),
        default_branch=data.get("default_branch", "main"),
        language=data.get("language"),
    )


def list_python_files(owner: str, repo: str, branch: str, max_files: int = 30) -> list[str]:
    resp = requests.get(
        f"{_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}",
        params={"recursive": "1"},
        headers=_headers(),
        timeout=20,
    )
    resp.raise_for_status()
    tree = resp.json().get("tree", [])
    paths = [
        item["path"]
        for item in tree
        if item.get("type") == "blob" and item["path"].endswith(".py")
    ]
    return paths[:max_files]


def fetch_file_content(owner: str, repo: str, branch: str, path: str) -> str:
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.text
