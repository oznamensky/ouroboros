#!/usr/bin/env python3
"""
GitHub API Monitor for Ouroboros

Purpose: Monitor GitHub issues without relying on the `gh` CLI.
Usage: Check for new issues, list open issues, and provide issue details.
"""

import os
import sys
import json
import requests
from datetime import datetime

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_OWNER = "oznamensky"
REPO_NAME = "ouroboros"
API_BASE = "https://api.github.com"

def get_headers():
    """Return authentication headers for GitHub API."""
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Ouroboros-GitHub-Monitor"
    }

def list_issues(state="open", limit=50):
    """List issues from the repository."""
    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/issues"
    params = {"state": state, "per_page": limit}
    response = requests.get(url, headers=get_headers(), params=params)
    response.raise_for_status()
    return response.json()

def get_issue(number):
    """Get a specific issue by number."""
    url = f"{API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/issues/{number}"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json()

def check_rate_limit():
    """Check GitHub API rate limit."""
    url = f"{API_BASE}/rate_limit"
    response = requests.get(url, headers=get_headers())
    response.raise_for_status()
    return response.json()["rate"]

def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: github_monitor.py [list|get|rate] [args]")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "list":
            state = sys.argv[2] if len(sys.argv) > 2 else "open"
            issues = list_issues(state=state)
            print(json.dumps(issues, indent=2))
        elif command == "get":
            if len(sys.argv) < 3:
                print("Usage: github_monitor.py get <issue_number>")
                sys.exit(1)
            issue_num = int(sys.argv[2])
            issue = get_issue(issue_num)
            print(json.dumps(issue, indent=2))
        elif command == "rate":
            rate = check_rate_limit()
            print(json.dumps(rate, indent=2))
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Value Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()