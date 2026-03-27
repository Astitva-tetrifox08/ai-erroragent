import requests
from utils.logger import get_logger

logger = get_logger("teams_notifier")


def notify_teams(webhook_url: str, title: str, error_summary: dict, ai_fix: str):
    facts = [
        {"title": "Severity", "value": error_summary.get("severity") or "N/A"},
        {"title": "Project", "value": error_summary.get("project_name") or "N/A"},
        {"title": "Exception", "value": error_summary.get("exception_type") or "N/A"},
        {"title": "Message", "value": error_summary.get("message") or "N/A"},
        {"title": "File", "value": error_summary.get("file") or "N/A"},
        {"title": "Line", "value": str(error_summary.get("line_number") or "N/A")},
        {"title": "Repository", "value": error_summary.get("github_repo") or "N/A"},
    ]

    card = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "size": "Large",
                            "weight": "Bolder",
                            "color": "Attention",
                            "text": title,
                        },
                        {
                            "type": "FactSet",
                            "facts": facts,
                        },
                        {
                            "type": "TextBlock",
                            "text": "AI Suggested Fix",
                            "weight": "Bolder",
                            "spacing": "Large",
                        },
                        {
                            "type": "TextBlock",
                            "text": ai_fix,
                            "wrap": True,
                            "fontType": "Monospace",
                            "size": "Small",
                        },
                    ],
                },
            }
        ],
    }

    response = requests.post(webhook_url, json=card, timeout=60)

    if response.status_code in (200, 202):
        logger.info("Teams notification sent")
    else:
        logger.error(f"Teams notification failed: {response.status_code} {response.text}")
