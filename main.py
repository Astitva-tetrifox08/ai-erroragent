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

    parsed = {
        "message": essentials.get("alertRule"),
        "severity": essentials.get("severity"),
        "project_name": context.get("resourceName"),
        "service_url": None,
        "github_link": None,
        "file": None,
    }
    logger.info(f"Project: {parsed.get('project_name')}")

    repo = resolver.resolve(parsed)
    if repo == "UNKNOWN_REPO":
        logger.error(f"Could not resolve repo for: {parsed.get('project_name')}")
        return {"status": "repo_not_found"}
    logger.info(f"Resolved repo: {repo}")

    try:
        repo_code = fetcher.fetch_repo_code(repo)
        if not repo_code.strip():
            logger.warning("No code found in repo")
            return {"status": "no_code_found"}
    except Exception:
        logger.error("Failed to fetch repo code", exc_info=True)
        return {"status": "fetch_failed"}

    try:
        ai_response = ask_github_models(parsed, repo_code)
        logger.info("AI analysis complete")
    except Exception:
        logger.error("AI analysis failed", exc_info=True)
        return {"status": "ai_failed"}

    try:
        notify_teams(
            webhook_url=TEAMS_WEBHOOK_URL,
            title="Azure Production Alert",
            error_summary={
                "message": parsed.get("message"),
                "severity": parsed.get("severity"),
                "project_name": parsed.get("project_name"),
                "github_repo": repo,
            },
            ai_fix=ai_response,
        )
        logger.info("Teams notification sent")
    except Exception:
        logger.error("Failed to notify Teams", exc_info=True)
        return {"status": "teams_failed"}

    return {"status": "success"}
