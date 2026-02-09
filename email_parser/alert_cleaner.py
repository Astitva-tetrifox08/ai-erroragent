def clean_alert_email(text: str) -> str:
    """
    Keep content until Message section (inclusive)
    """

    lines = text.splitlines()
    cleaned = []
    keep = True

    for line in lines:
        cleaned.append(line)

        
        if line.strip().lower().startswith("unsubscribe"):
            break

    return "\n".join(cleaned).strip()
