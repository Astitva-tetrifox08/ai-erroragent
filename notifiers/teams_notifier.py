import requests


def notify_teams(webhook_url: str, title: str, error_summary: dict, ai_fix: str):
    """
    Send error + AI fix to Microsoft Teams
    """

    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "summary": title,
        "themeColor": "E81123",
        "title": title,
        "sections": [
            {
                "activityTitle": "🚨 Error Detected",
                "facts": [
                    {"name": "Error Message", "value": error_summary.get("message")},
                    {"name": "File", "value": error_summary.get("file")},
                    {"name": "Service", "value": error_summary.get("service_url")},
                    {"name": "GitHub Repo", "value": error_summary.get("github_link")},
                ],
                "markdown": True
            },
            {
                "activityTitle": "🤖 AI Suggested Fix",
                "text": f"```\n{ai_fix}\n```",
                "markdown": True
            }
        ]
    }

    response = requests.post(webhook_url, json=message)

    if response.status_code == 200:
        print("✅ Notification sent to Microsoft Teams")
    else:
        print("❌ Failed to send Teams notification")
        print(response.text)
