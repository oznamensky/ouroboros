"""Test script to debug GitHub tools."""
import sys
sys.path.insert(0, '/content/ouroboros_repo')

from ouroboros.tools.github import _gh_cmd, _list_issues_cli, _list_issues

class MockCtx:
    repo_dir = '/content/ouroboros_repo'

ctx = MockCtx()

# Test _gh_cmd
print("Testing _gh_cmd...")
result = _gh_cmd(['issue', 'list'], ctx)
print(f"Result: {repr(result)}")
print(f"Starts with GH_ERROR check: {result.startswith('⚠️ GH_ERROR: `gh` CLI not found.')}")

# Test _list_issues_cli
print("\nTesting _list_issues_cli...")
result2 = _list_issues_cli(ctx, 'open', '', 20)
print(f"Result: {repr(result2)}")

# Test _list_issues
print("\nTesting _list_issues...")
result3 = _list_issues(ctx, 'open', '', 20)
print(f"Result: {repr(result3)}")
