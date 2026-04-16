"""GitHub tools: issues, comments, reactions."""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.parse

from ouroboros.tools.registry import ToolContext, ToolEntry

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# GitHub API Helpers
# ---------------------------------------------------------------------------

def _get_repo_slug(ctx: ToolContext) -> str:
    """Get 'owner/repo' from git remote or environment."""
    try:
        # Try to get from gh CLI first
        res = subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            cwd=str(ctx.repo_dir),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        log.debug("Failed to get repo slug from gh", exc_info=True)
    
    # Fallback to environment or git remote
    user = os.environ.get("GITHUB_USER", "")
    repo = os.environ.get("GITHUB_REPO", "")
    if user and repo:
        return f"{user}/{repo}"
    
    # Try to extract from git remote
    try:
        res = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(ctx.repo_dir),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if res.returncode == 0:
            url = res.stdout.strip()
            # Parse GitHub URL
            for pattern in [
                r"git@github\.com:([^/]+)/([^\.]+)\.git",
                r"https://github\.com/([^/]+)/([^\.]+)",
                r"git://github\.com/([^/]+)/([^\.]+)",
            ]:
                match = re.match(pattern, url)
                if match:
                    return f"{match.group(1)}/{match.group(2)}"
    except Exception:
        log.debug("Failed to parse git remote", exc_info=True)
    
    return "unknown/repo"


def _github_api_request(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None
) -> tuple[int, str]:
    """
    Make a GitHub API request.
    Returns (status_code, response_body).
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return 0, "⚠️ No GITHUB_TOKEN environment variable found."
    
    base_url = "https://api.github.com"
    url = base_url + endpoint
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Ouroboros-GitHub-Tool/1.0",
    }
    
    try:
        if data and method == "GET":
            # Convert data to query parameters
            query_string = urllib.parse.urlencode(data)
            url = f"{url}?{query_string}"
            data_bytes = None
        elif data:
            data_bytes = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        else:
            data_bytes = None
        
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            status_code = response.status
            response_body = response.read().decode("utf-8")
            return status_code, response_body
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        return e.code, f"⚠️ GitHub API error ({e.code}): {error_body}"
    
    except urllib.error.URLError as e:
        return 0, f"⚠️ Network error: {e.reason}"
    
    except Exception as e:
        return 0, f"⚠️ Unexpected error: {e}"


# ---------------------------------------------------------------------------
# Fallback API Functions
# ---------------------------------------------------------------------------

def _list_issues_api(ctx: ToolContext, state: str = "open", labels: str = "", limit: int = 20) -> str:
    """List GitHub issues using API fallback."""
    repo_slug = _get_repo_slug(ctx)
    if repo_slug == "unknown/repo":
        return "⚠️ Could not determine repository. Set GITHUB_USER and GITHUB_REPO environment variables."
    
    endpoint = f"/repos/{repo_slug}/issues"
    params = {"state": state, "per_page": min(limit, 50)}
    if labels:
        params["labels"] = labels
    
    # Add query parameters to endpoint
    query_string = urllib.parse.urlencode(params)
    endpoint = f"{endpoint}?{query_string}"
    
    status_code, response = _github_api_request(endpoint)
    
    if status_code != 200:
        return f"⚠️ Failed to list issues: {response}"
    
    try:
        issues = json.loads(response)
    except json.JSONDecodeError:
        return f"⚠️ Failed to parse issues JSON: {response[:500]}"
    
    if not issues:
        return f"No {state} issues found."
    
    lines = [f"**{len(issues)} {state} issue(s):**\n"]
    for issue in issues:
        labels_str = ", ".join(l.get("name", "") for l in issue.get("labels", []))
        author = issue.get("user", {}).get("login", "unknown")
        lines.append(
            f"- **#{issue['number']}** {issue['title']}"
            f" (by @{author}{', labels: ' + labels_str if labels_str else ''})"
        )
        body = (issue.get("body") or "").strip()
        if body:
            # Show first 200 chars of body
            preview = body[:200] + ("..." if len(body) > 200 else "")
            lines.append(f"  > {preview}")
    
    return "\n".join(lines)


def _get_issue_api(ctx: ToolContext, number: int) -> str:
    """Get a single issue using API fallback."""
    if number <= 0:
        return "⚠️ issue number must be positive"
    
    repo_slug = _get_repo_slug(ctx)
    if repo_slug == "unknown/repo":
        return "⚠️ Could not determine repository. Set GITHUB_USER and GITHUB_REPO environment variables."
    
    endpoint = f"/repos/{repo_slug}/issues/{number}"
    status_code, response = _github_api_request(endpoint)
    
    if status_code != 200:
        return f"⚠️ Failed to get issue #{number}: {response}"
    
    try:
        issue = json.loads(response)
    except json.JSONDecodeError:
        return f"⚠️ Failed to parse issue JSON: {response[:500]}"
    
    labels_str = ", ".join(l.get("name", "") for l in issue.get("labels", []))
    author = issue.get("user", {}).get("login", "unknown")
    
    lines = [
        f"## Issue #{issue['number']}: {issue['title']}",
        f"**State:** {issue['state']}  |  **Author:** @{author}",
    ]
    if labels_str:
        lines.append(f"**Labels:** {labels_str}")
    
    body = (issue.get("body") or "").strip()
    if body:
        lines.append(f"\n**Body:**\n{body[:3000]}")
    
    # Get comments
    comments_endpoint = f"/repos/{repo_slug}/issues/{number}/comments"
    status_code, comments_response = _github_api_request(comments_endpoint)
    if status_code == 200:
        try:
            comments = json.loads(comments_response)
            if comments:
                lines.append(f"\n**Comments ({len(comments)}):**")
                for c in comments[:10]:  # limit to 10 most recent
                    c_author = c.get("user", {}).get("login", "unknown")
                    c_body = (c.get("body") or "").strip()[:500]
                    lines.append(f"\n@{c_author}:\n{c_body}")
        except json.JSONDecodeError:
            pass
    
    return "\n".join(lines)


def _comment_on_issue_api(ctx: ToolContext, number: int, body: str) -> str:
    """Add a comment to an issue using API fallback."""
    if number <= 0:
        return "⚠️ issue number must be positive"
    
    if not body or not body.strip():
        return "⚠️ Comment body cannot be empty."
    
    repo_slug = _get_repo_slug(ctx)
    if repo_slug == "unknown/repo":
        return "⚠️ Could not determine repository. Set GITHUB_USER and GITHUB_REPO environment variables."
    
    endpoint = f"/repos/{repo_slug}/issues/{number}/comments"
    data = {"body": body}
    
    status_code, response = _github_api_request(endpoint, method="POST", data=data)
    
    if status_code != 201:
        return f"⚠️ Failed to add comment: {response}"
    
    return f"✅ Comment added to issue #{number}."


def _close_issue_api(ctx: ToolContext, number: int, comment: str = "") -> str:
    """Close an issue with optional closing comment using API fallback."""
    if number <= 0:
        return "⚠️ issue number must be positive"
    
    repo_slug = _get_repo_slug(ctx)
    if repo_slug == "unknown/repo":
        return "⚠️ Could not determine repository. Set GITHUB_USER and GITHUB_REPO environment variables."
    
    # Add comment first if provided
    if comment and comment.strip():
        result = _comment_on_issue_api(ctx, number, comment)
        if result.startswith("⚠️"):
            return result
    
    endpoint = f"/repos/{repo_slug}/issues/{number}"
    data = {"state": "closed"}
    
    status_code, response = _github_api_request(endpoint, method="PATCH", data=data)
    
    if status_code != 200:
        return f"⚠️ Failed to close issue #{number}: {response}"
    
    return f"✅ Issue #{number} closed."


def _create_issue_api(ctx: ToolContext, title: str, body: str = "", labels: str = "") -> str:
    """Create a new GitHub issue using API fallback."""
    if not title or not title.strip():
        return "⚠️ Issue title cannot be empty."
    
    repo_slug = _get_repo_slug(ctx)
    if repo_slug == "unknown/repo":
        return "⚠️ Could not determine repository. Set GITHUB_USER and GITHUB_REPO environment variables."
    
    endpoint = f"/repos/{repo_slug}/issues"
    data = {"title": title}
    if body:
        data["body"] = body
    if labels:
        data["labels"] = [label.strip() for label in labels.split(",")]
    
    status_code, response = _github_api_request(endpoint, method="POST", data=data)
    
    if status_code != 201:
        return f"⚠️ Failed to create issue: {response}"
    
    try:
        issue_data = json.loads(response)
        issue_num = issue_data.get("number", "unknown")
        issue_url = issue_data.get("html_url", "unknown")
        return f"✅ Issue #{issue_num} created: {issue_url}"
    except json.JSONDecodeError:
        return f"✅ Issue created: {response[:500]}"


# ---------------------------------------------------------------------------
# CLI-based Functions (original)
# ---------------------------------------------------------------------------

def _gh_cmd(args: List[str], ctx: ToolContext, timeout: int = 30, input_data: Optional[str] = None) -> str:
    """Run `gh` CLI command and return stdout or error string."""
    cmd = ["gh"] + args
    try:
        res = subprocess.run(
            cmd,
            cwd=str(ctx.repo_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
            input=input_data,
        )
        if res.returncode != 0:
            err = (res.stderr or "").strip()
            # Only return first line of stderr, truncated to 200 chars for security
            return f"⚠️ GH_ERROR: {err.split(chr(10))[0][:200]}"
        return res.stdout.strip()
    except FileNotFoundError:
        return "⚠️ GH_ERROR: `gh` CLI not found."
    except subprocess.TimeoutExpired:
        return f"⚠️ GH_TIMEOUT: exceeded {timeout}s."
    except Exception as e:
        return f"⚠️ GH_ERROR: {e}"


def _list_issues_cli(ctx: ToolContext, state: str = "open", labels: str = "", limit: int = 20) -> str:
    """List GitHub issues using gh CLI."""
    args = [
        "issue", "list",
        "--state", state,
        "--limit", str(min(limit, 50)),
        "--json", "number,title,body,labels,createdAt,author,assignees,state",
    ]
    if labels:
        args.extend(["--label", labels])

    raw = _gh_cmd(args, ctx)
    if raw.startswith("⚠️"):
        return raw

    try:
        issues = json.loads(raw)
    except json.JSONDecodeError:
        return f"⚠️ Failed to parse issues JSON: {raw[:500]}"

    if not issues:
        return f"No {state} issues found."

    lines = [f"**{len(issues)} {state} issue(s):**\n"]
    for issue in issues:
        labels_str = ", ".join(l.get("name", "") for l in issue.get("labels", []))
        author = issue.get("author", {}).get("login", "unknown")
        lines.append(
            f"- **#{issue['number']}** {issue['title']}"
            f" (by @{author}{', labels: ' + labels_str if labels_str else ''})"
        )
        body = (issue.get("body") or "").strip()
        if body:
            # Show first 200 chars of body
            preview = body[:200] + ("..." if len(body) > 200 else "")
            lines.append(f"  > {preview}")

    return "\n".join(lines)


def _get_issue_cli(ctx: ToolContext, number: int) -> str:
    """Get a single issue using gh CLI."""
    if number <= 0:
        return "⚠️ issue number must be positive"

    args = [
        "issue", "view", str(number),
        "--json", "number,title,body,labels,createdAt,author,assignees,state,comments",
    ]

    raw = _gh_cmd(args, ctx)
    if raw.startswith("⚠️"):
        return raw

    try:
        issue = json.loads(raw)
    except json.JSONDecodeError:
        return f"⚠️ Failed to parse issue JSON: {raw[:500]}"

    labels_str = ", ".join(l.get("name", "") for l in issue.get("labels", []))
    author = issue.get("author", {}).get("login", "unknown")

    lines = [
        f"## Issue #{issue['number']}: {issue['title']}",
        f"**State:** {issue['state']}  |  **Author:** @{author}",
    ]
    if labels_str:
        lines.append(f"**Labels:** {labels_str}")

    body = (issue.get("body") or "").strip()
    if body:
        lines.append(f"\n**Body:**\n{body[:3000]}")

    comments = issue.get("comments", [])
    if comments:
        lines.append(f"\n**Comments ({len(comments)}):**")
        for c in comments[:10]:  # limit to 10 most recent
            c_author = c.get("author", {}).get("login", "unknown")
            c_body = (c.get("body") or "").strip()[:500]
            lines.append(f"\n@{c_author}:\n{c_body}")

    return "\n".join(lines)


def _comment_on_issue_cli(ctx: ToolContext, number: int, body: str) -> str:
    """Add a comment to an issue using gh CLI."""
    if number <= 0:
        return "⚠️ issue number must be positive"

    if not body or not body.strip():
        return "⚠️ Comment body cannot be empty."

    # Pass body via stdin to prevent argument injection
    args = ["issue", "comment", str(number), "--body-file", "-"]
    raw = _gh_cmd(args, ctx, input_data=body)
    if raw.startswith("⚠️"):
        return raw
    return f"✅ Comment added to issue #{number}."


def _close_issue_cli(ctx: ToolContext, number: int, comment: str = "") -> str:
    """Close an issue with optional closing comment using gh CLI."""
    if number <= 0:
        return "⚠️ issue number must be positive"

    if comment and comment.strip():
        # Add comment first, then close
        comment_result = _comment_on_issue_cli(ctx, number, comment)
        if comment_result.startswith("⚠️"):
            return comment_result

    args = ["issue", "close", str(number)]
    raw = _gh_cmd(args, ctx)
    if raw.startswith("⚠️"):
        return raw
    return f"✅ Issue #{number} closed."


def _create_issue_cli(ctx: ToolContext, title: str, body: str = "", labels: str = "") -> str:
    """Create a new GitHub issue using gh CLI."""
    if not title or not title.strip():
        return "⚠️ Issue title cannot be empty."

    args = ["issue", "create", "--title", title]
    if body:
        args.extend(["--body", body])
    if labels:
        for label in labels.split(","):
            args.extend(["--label", label.strip()])

    raw = _gh_cmd(args, ctx)
    if raw.startswith("⚠️"):
        return raw

    # Extract issue number from URL or response
    # gh CLI returns the issue URL
    return f"✅ Issue created: {raw}"


# ---------------------------------------------------------------------------
# Unified Functions with Automatic Fallback
# ---------------------------------------------------------------------------

def _list_issues(ctx: ToolContext, state: str = "open", labels: str = "", limit: int = 20) -> str:
    """List GitHub issues - tries CLI first, falls back to API."""
    # Try CLI first
    result = _list_issues_cli(ctx, state, labels, limit)
    if result.startswith("⚠️ GH_ERROR: `gh` CLI not found."):
        # Fall back to API
        return _list_issues_api(ctx, state, labels, limit)
    return result


def _get_issue(ctx: ToolContext, number: int) -> str:
    """Get a single issue - tries CLI first, falls back to API."""
    # Try CLI first
    result = _get_issue_cli(ctx, number)
    if result.startswith("⚠️ GH_ERROR: `gh` CLI not found."):
        # Fall back to API
        return _get_issue_api(ctx, number)
    return result


def _comment_on_issue(ctx: ToolContext, number: int, body: str) -> str:
    """Add a comment to an issue - tries CLI first, falls back to API."""
    # Try CLI first
    result = _comment_on_issue_cli(ctx, number, body)
    if result.startswith("⚠️ GH_ERROR: `gh` CLI not found."):
        # Fall back to API
        return _comment_on_issue_api(ctx, number, body)
    return result


def _close_issue(ctx: ToolContext, number: int, comment: str = "") -> str:
    """Close an issue - tries CLI first, falls back to API."""
    # Try CLI first
    result = _close_issue_cli(ctx, number, comment)
    if result.startswith("⚠️ GH_ERROR: `gh` CLI not found."):
        # Fall back to API
        return _close_issue_api(ctx, number, comment)
    return result


def _create_issue(ctx: ToolContext, title: str, body: str = "", labels: str = "") -> str:
    """Create a new GitHub issue - tries CLI first, falls back to API."""
    # Try CLI first
    result = _create_issue_cli(ctx, title, body, labels)
    if result.startswith("⚠️ GH_ERROR: `gh` CLI not found."):
        # Fall back to API
        return _create_issue_api(ctx, title, body, labels)
    return result


# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

def get_tools() -> List[ToolEntry]:
    return [
        ToolEntry("list_github_issues", {
            "name": "list_github_issues",
            "description": "List GitHub issues. Use to check for new tasks, bug reports, or feature requests from the creator or contributors.",
            "parameters": {"type": "object", "properties": {
                "state": {"type": "string", "default": "open", "enum": ["open", "closed", "all"], "description": "Filter by state"},
                "labels": {"type": "string", "default": "", "description": "Filter by label (comma-separated)"},
                "limit": {"type": "integer", "default": 20, "description": "Max issues to return (max 50)"},
            }, "required": []},
        }, _list_issues),

        ToolEntry("get_github_issue", {
            "name": "get_github_issue",
            "description": "Get full details of a GitHub issue including body and comments.",
            "parameters": {"type": "object", "properties": {
                "number": {"type": "integer", "description": "Issue number"},
            }, "required": ["number"]},
        }, _get_issue),

        ToolEntry("comment_on_issue", {
            "name": "comment_on_issue",
            "description": "Add a comment to a GitHub issue. Use to respond to issues, share progress, or ask clarifying questions.",
            "parameters": {"type": "object", "properties": {
                "number": {"type": "integer", "description": "Issue number"},
                "body": {"type": "string", "description": "Comment text (markdown)"},
            }, "required": ["number", "body"]},
        }, _comment_on_issue),

        ToolEntry("close_github_issue", {
            "name": "close_github_issue",
            "description": "Close a GitHub issue with optional closing comment.",
            "parameters": {"type": "object", "properties": {
                "number": {"type": "integer", "description": "Issue number"},
                "comment": {"type": "string", "default": "", "description": "Optional closing comment"},
            }, "required": ["number"]},
        }, _close_issue),

        ToolEntry("create_github_issue", {
            "name": "create_github_issue",
            "description": "Create a new GitHub issue. Use for tracking tasks, documenting bugs, or planning features.",
            "parameters": {"type": "object", "properties": {
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "default": "", "description": "Issue body (markdown)"},
                "labels": {"type": "string", "default": "", "description": "Labels (comma-separated)"},
            }, "required": ["title"]},
        }, _create_issue),
    ]
