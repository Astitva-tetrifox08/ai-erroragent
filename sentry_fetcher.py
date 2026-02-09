import requests

def fetch_sentry_issue(url: str) -> str:
    # ✅ Only allow Sentry domains
    if "sentry.io" not in url:
        raise ValueError("Not a Sentry URL. Skipping fetch.")

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 403:
        raise RuntimeError("Sentry page is private or requires auth")

    response.raise_for_status()
    return response.text
