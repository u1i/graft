#!/usr/bin/env python3
"""Quick test to check if API key is valid"""

import requests
import configparser
from pathlib import Path

# Load API key
config_path = Path.home() / '.graft_cfg'
config = configparser.ConfigParser()
config.read(config_path)
api_key = config.get('openrouter', 'api_key')

print(f"Testing API key: {api_key[:20]}...")
print()

# Test 1: Check if key works with models endpoint (doesn't require credits)
print("Test 1: Fetching models list (no credits needed)...")
headers = {
    "Authorization": f"Bearer {api_key}",
}

response = requests.get('https://openrouter.ai/api/v1/models', headers=headers, verify=False)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ API key is valid - models endpoint accessible")
else:
    print(f"❌ Error: {response.text[:200]}")

print()

# Test 2: Try a simple chat completion
print("Test 2: Testing chat completions endpoint...")
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

data = {
    "model": "openai/gpt-5-image",
    "messages": [
        {
            "role": "user",
            "content": "Singapore Merlion during a snow storm"
        }
    ]
}

response = requests.post('https://openrouter.ai/api/v1/chat/completions', 
                        headers=headers, json=data, verify=False)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("✅ Chat completions working")
elif response.status_code == 401:
    print("❌ 401 Unauthorized - API key issue")
    print(f"Response: {response.text}")
elif response.status_code == 402:
    print("❌ 402 Payment Required - No credits/insufficient balance")
    print(f"Response: {response.text}")
else:
    print(f"❌ Error {response.status_code}")
    print(f"Response: {response.text[:500]}")
