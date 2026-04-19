#!/usr/bin/env python3
import os
import sys
import urllib.request
import json

token = os.environ.get('GITHUB_TOKEN')
if not token:
    print("No GITHUB_TOKEN found")
    sys.exit(1)

# Test direct API call
endpoint = '/repos/oznamensky/ouroboros/issues?state=open&per_page=5'
url = f'https://api.github.com{endpoint}'
headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'Ouroboros-GitHub-Tool/1.0',
}
req = urllib.request.Request(url, headers=headers, method='GET')
try:
    with urllib.request.urlopen(req, timeout=10) as response:
        print(f'Status: {response.status}')
        body = response.read().decode('utf-8')
        print(f'Response length: {len(body)}')
        data = json.loads(body)
        print(f'Number of issues: {len(data)}')
        for issue in data:
            print(f'  #{issue["number"]}: {issue["title"]}')
except urllib.error.HTTPError as e:
    print(f'HTTP Error: {e.code} {e.reason}')
    print(f'Response: {e.read().decode("utf-8")[:500]}')
except Exception as e:
    print(f'Error: {e}')
