# ================= IMPORTS ================= #

from fastapi import FastAPI, Request
from repo_resolver.resolver import RepoResolver
from github.github_fetcher import GitHubFetcher
from github.github_models_client import ask_github_models
from notifiers.teams_notifier import notify_teams
from utils.logger import setup_logging, get_logger

# ================= SETUP LOGGING ================= #

setup_logging()
logger = get_logger("main")
logger.info("🔥 MAIN FILE VERSION V9 🔥")

# ================= FASTAPI APP ================= #

app = FastAPI()

# ================= CONFIG ================= #

TEAMS_WEBHOOK_URL = (
    "https://synoptechbusiness.webhook.office.com/webhookb2/"
    "45b65599-b77b-497a-93c7-b0d662277619@e001af36-37b7-49be-961e-1881605dc83a/"
    "IncomingWebhook/626bb7cbb2cf41aea9e32b2bf813ebe1/"
    "faefc126-436c-4f27-ad2d-ee1d1b3066ab/V2AMy5S0eCmK97aaBnXCk2KcXtTaqajPvYJ0uI4aS1PBg1"
)

# ================= HEALTH CHECK ================= #

@app.get("/")
def health():
    return {"status": "AI Agent is running 🚀"}

# ================= AZURE WEBHOOK ENDPOINT ================= #

@app.post("/azure/alert")
async def azure_alert(request: Request):

    logger.info("🚨 Azure alert received")

    # ---------- READ PAYLOAD ---------- #
    try:
        payload = await request.json()
        logger.debug(f"Full payload: {payload}")

    except Exception:
        logger.error("❌ Failed to read Azure payload", exc_info=True)
        return {"status": "invalid_payload"}

    # ---------- PARSE AZURE ALERT ---------- #
    try:
        essentials = payload.get("data", {}).get("essentials", {})
        context = payload.get("data", {}).get("alertContext", {})

        parsed = {
            "is_error": True,
            "message": essentials.get("alertRule"),
            "file": None,
            "severity": essentials.get("severity"),
            "service_url": None,
            "github_link": None,
            "project_name": context.get("resourceName"),
            "alert_name": essentials.get("alertRule")
        }

        logger.info("✅ Azure alert parsed successfully")
        logger.info(f"📌 Incoming project_name: {parsed.get('project_name')}")
        logger.debug(parsed)

    except Exception:
        logger.error("❌ Azure parsing failed", exc_info=True)
        return {"status": "parse_failed"}

    # ---------- RESOLVE REPOSITORY ---------- #
    try:
        resolver = RepoResolver()
        repo = resolver.resolve(parsed)

        if repo == "UNKNOWN_REPO":
            logger.error(f"❌ Repository could not be resolved for project: {parsed.get('project_name')}")
            return {"status": "repo_not_found"}

        logger.info(f"✅ Resolved repository: {repo}")

    except Exception:
        logger.error("❌ Repository resolution failed", exc_info=True)
        return {"status": "repo_resolution_failed"}

    # ---------- FETCH REPO CODE ---------- #
    try:
        fetcher = GitHubFetcher()
        repo_code = fetcher.fetch_repo_code(repo, None)

        if not repo_code.strip():
            logger.warning("⚠️ No repository code found")
            return {"status": "no_code_found"}

        logger.info("✅ Repository code fetched successfully")

    except Exception:
        logger.error("❌ Failed to fetch repository code", exc_info=True)
        return {"status": "fetch_failed"}

    # ---------- AI ANALYSIS ---------- #
    try:
        ai_response = ask_github_models(parsed, repo_code)

        logger.info("✅ AI suggestion received")
        logger.debug(ai_response)

    except Exception:
        logger.error("❌ AI analysis failed", exc_info=True)
        return {"status": "ai_failed"}

    # ---------- SEND TO TEAMS ---------- #
    try:
        notify_teams(
            webhook_url=TEAMS_WEBHOOK_URL,
            title="🚨 Azure Production Alert Detected",
            error_summary={
                "message": parsed.get("message"),
                "severity": parsed.get("severity"),
                "project_name": parsed.get("project_name"),
                "github_repo": repo
            },
            ai_fix=ai_response
        )

        logger.info("✅ Teams notification sent successfully")

    except Exception:
        logger.error("❌ Failed to notify Microsoft Teams", exc_info=True)
        return {"status": "teams_failed"}

    logger.info("🎉 Azure alert handled successfully")

    return {"status": "success"}