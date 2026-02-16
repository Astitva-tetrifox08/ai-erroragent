from fastapi import FastAPI, Request
from utils.logger import get_logger

from repo_resolver.resolver import RepoResolver
from github.github_fetcher import GitHubFetcher
from github.github_models_client import ask_github_models
from notifiers.teams_notifier import notify_teams

app = FastAPI()
logger = get_logger("azure-webhook")

TEAMS_WEBHOOK_URL = ""

@app.post("/azure/alert")
async def receive_alert(request: Request):

    payload = await request.json()

    logger.info("🚨 Azure alert received")
    logger.debug(payload)

    # STEP 1: Parse Azure JSON
    essentials = payload.get("data", {}).get("essentials", {})
    context = payload.get("data", {}).get("alertContext", {})

    parsed = {
        "is_error": True,
        "alert_name": essentials.get("alertRule"),
        "severity": essentials.get("severity"),
        "project_name": context.get("resourceName"),
        "service_url": None,
        "file": None,
        "message": essentials.get("alertRule")
    }

    logger.info("Parsed Azure alert")

    # STEP 2: Resolve Repo
    resolver = RepoResolver()
    repo = resolver.resolve(parsed)

    if repo == "UNKNOWN_REPO":
        logger.error("Repo not found")
        return {"status": "repo_not_found"}

    logger.info(f"Resolved repo: {repo}")

    # STEP 3: Fetch Code
    fetcher = GitHubFetcher()
    repo_code = fetcher.fetch_repo_code(repo, None)

    # STEP 4: AI Analysis
    ai_response = ask_github_models(parsed, repo_code)

    # STEP 5: Send to Teams
    notify_teams(
        webhook_url=TEAMS_WEBHOOK_URL,
        title="🚨 Azure Production Alert",
        error_summary=parsed,
        ai_fix=ai_response
    )

    logger.info("✅ Alert processed successfully")

    return {"status": "success"}
