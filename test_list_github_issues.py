#!/usr/bin/env python3
import os
import sys

# Add the repo root to path
sys.path.insert(0, '/content/ouroboros_repo')

from ouroboros.tools.github import get_tools

# Get the tool function
tools = get_tools()
list_github_issues_tool = None
for tool in tools:
    if tool.name == "list_github_issues":
        list_github_issues_tool = tool
        break

if not list_github_issues_tool:
    print("ERROR: list_github_issues tool not found")
    sys.exit(1)

# Create a mock context
class MockContext:
    def __init__(self):
        self.repo_dir = "/content/ouroboros_repo"
        self.chat_id = 40441821

ctx = MockContext()

# Call the tool
try:
    result = list_github_issues_tool.fn(ctx)
    print(f"Tool result: {result}")
except Exception as e:
    print(f"Tool error: {e}")
