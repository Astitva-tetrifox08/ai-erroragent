import os
import requests
import json

GITHUB_MODELS_URL = "https://models.inference.ai.azure.com/chat/completions"

def ask_github_models(parsed_error: dict, repo_code: str) -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("❌ GITHUB_TOKEN not set")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    prompt = f"""
You are a senior software engineer.

An error occurred in production.

Error details:
{json.dumps(parsed_error, indent=2)}

Relevant code:
{repo_code[:12000]}

Tasks:
1. Explain the root cause
2. Point to the file and line
3. Suggest a fix
4. Provide corrected code snippet
"""

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are an expert debugging assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    response = requests.post(
        GITHUB_MODELS_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]
