import re

def parse_error(text: str) -> dict:
    result = {
        "is_error": False,
        "error_type": None,
        "message": None,
        "file": None,
        "service_url": None,
        "github_link": None,
        "project_name": None,
        "alert_name": None,
        "severity": "UNKNOWN"
    }

    clean = re.sub(r"<[^>]+>", "", text)

    if re.search(r"error|exception|failure|alert", clean, re.I):
        result["is_error"] = True
        result["message"] = "Error detected"

    # Severity
    sev = re.search(r"Sev\d|Critical|High", clean, re.I)
    if sev:
        result["severity"] = sev.group(0)

    # Alert name (Azure)
    alert = re.search(r"Alert name\s*\n\s*(.+)", clean)
    if alert:
        result["alert_name"] = alert.group(1).strip()

    # Project / resource
    resource = re.search(r"Affected resource\s*\n\s*([a-zA-Z0-9\-]+)", clean)
    if resource:
        result["project_name"] = resource.group(1)

    # File path (stacktrace)
    file_match = re.search(r'File\s+"([^"]+\.py)"', clean)
    if file_match:
        result["file"] = file_match.group(1)

    # Service URL
    url = re.search(r"https://[a-zA-Z0-9.\-]+", clean)
    if url:
        result["service_url"] = url.group(0)

    # GitHub link
    gh = re.search(r"https://github\.com/[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+", clean)
    if gh:
        result["github_link"] = gh.group(0)

    return result
