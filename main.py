import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request

load_dotenv()
from repo_resolver.resolver import RepoResolver
from github.github_fetcher import GitHubFetcher
from github.github_models_client import ask_github_models
from notifiers.teams_notifier import notify_teams
from utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger("main")

app = FastAPI()

TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")
if not TEAMS_WEBHOOK_URL:
    raise RuntimeError("TEAMS_WEBHOOK_URL environment variable is required")

resolver = RepoResolver()
fetcher = GitHubFetcher()


@app.get("/")
def health():
    return {"status": "running", "repos_loaded": len(resolver.repos)}


@app.post("/azure/alert")
async def azure_alert(request: Request):
    logger.info("Azure alert received")

    try:
        payload = await request.json()
        logger.debug(f"Payload: {payload}")
    except Exception:
        logger.error("Failed to read payload", exc_info=True)
        return {"status": "invalid_payload"}

    essentials = payload.get("data", {}).get("essentials", {})
    context = payload.get("data", {}).get("alertContext", {})

    # Extract exception details from alert dimensions
    dimensions = {}
    condition = context.get("condition", {})
    for criteria in condition.get("allOf", []):
        for dim in criteria.get("dimensions", []):
            dimensions[dim.get("name")] = dim.get("value")

    parsed = {
        "message": dimensions.get("ExceptionMessage") or essentials.get("alertRule"),
        "exception_type": dimensions.get("ExceptionType"),
        "severity": essentials.get("severity"),
        "project_name": dimensions.get("AppName") or context.get("resourceName") or essentials.get("targetResourceName"),
        "file": dimensions.get("FilePath"),
        "line_number": dimensions.get("LineNumber"),
        "service_url": None,
        "github_link": None,
    }

    logger.info(f"Project: {parsed.get('project_name')}, "
                f"Exception: {parsed.get('exception_type')}: {parsed.get('message', '')[:100]}")

    if not parsed.get("project_name"):
        logger.error("Could not extract project name from alert")
        return {"status": "no_project_name"}

    # Resolve repo
    repo = resolver.resolve(parsed)
    if repo == "UNKNOWN_REPO":
        logger.error(f"Could not resolve repo for: {parsed.get('project_name')}")
        return {"status": "repo_not_found"}
    logger.info(f"Resolved repo: {repo}")

    #  Fetch code (specific file first, then full repo)
    try:
        repo_code = ""
        if parsed.get("file"):
            repo_code = fetcher.fetch_repo_code(repo, parsed["file"])
        if not repo_code.strip():
            repo_code = fetcher.fetch_repo_code(repo)
        if not repo_code.strip():
            logger.warning("No code found in repo")
            return {"status": "no_code_found"}
    except Exception:
        logger.error("Failed to fetch repo code", exc_info=True)
        return {"status": "fetch_failed"}

    #  AI analysis
    try:
        ai_response = ask_github_models(parsed, repo_code)
        logger.info("AI analysis complete")
    except Exception:
        logger.error("AI analysis failed", exc_info=True)
        return {"status": "ai_failed"}

    #  Send to Teams
    try:
        notify_teams(
            webhook_url=TEAMS_WEBHOOK_URL,
            title="Azure Production Alert",
            error_summary={
                "message": parsed.get("message"),
                "exception_type": parsed.get("exception_type"),
                "severity": parsed.get("severity"),
                "project_name": parsed.get("project_name"),
                "github_repo": repo,
                "file": parsed.get("file"),
                "line_number": parsed.get("line_number"),
            },
            ai_fix=ai_response,
        )
        logger.info("Teams notification sent")
    except Exception:
        logger.error("Failed to notify Teams", exc_info=True)
        return {"status": "teams_failed"}

    return {"status": "success"}
