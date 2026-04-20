#!/usr/bin/env python3
"""Test GitHub API fallback."""

import sys
import os
sys.path.insert(0, '.')

# Set environment variables
os.environ['GITHUB_USER'] = 'oznamensky'
os.environ['GITHUB_REPO'] = 'ouroboros'

from ouroboros.tools.github import _list_issues_api, _github_api_request, _get_repo_slug
from unittest.mock import Mock

# Create a mock context
ctx = Mock()
ctx.repo_dir = '.'

# Test the API
print("Testing _list_issues_api...")
result = _list_issues_api(ctx, 'open', '', 20)
print("API Result:", result)

# Test _github_api_request directly
print("\nTesting _github_api_request...")
response = _github_api_request(ctx, 'GET', '/repos/oznamensky/ouroboros/issues?state=open&per_page=20')
print("Response:", response)
