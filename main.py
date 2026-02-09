# ================= IMPORTS ================= #

from email_service.email_reader import EmailReader
from email_parser.generic_error_parser import parse_error
from repo_resolver.resolver import RepoResolver
from sentry_fetcher import fetch_sentry_issue
from github.github_fetcher import GitHubFetcher
from github.github_models_client import ask_github_models
from notifiers.teams_notifier import notify_teams

from utils.logger import setup_logging, get_logger

setup_logging()              # 🔥 THIS WAS MISSING
logger = get_logger("main")


# ================= CONFIG ================= #

EMAIL = "maurya.astitva@gmail.com"
APP_PASSWORD = "qqwc iagi thfe gkjw"

TEAMS_WEBHOOK_URL = (
    "https://synoptechbusiness.webhook.office.com/webhookb2/"
    "45b65599-b77b-497a-93c7-b0d662277619@e001af36-37b7-49be-961e-1881605dc83a/"
    "IncomingWebhook/626bb7cbb2cf41aea9e32b2bf813ebe1/"
    "faefc126-436c-4f27-ad2d-ee1d1b3066ab/V2AMy5S0eCmK97aaBnXCk2KcXtTaqajPvYJ0uI4aS1PBg1"
)


# ================= MAIN FLOW ================= #

def main():
    logger.info("🚀 AI Agent started")

    # ---------- 1️⃣ READ EMAIL ---------- #
    try:
        logger.info("Reading latest email")

        reader = EmailReader(EMAIL, APP_PASSWORD)
        raw_email = reader.read_latest_email()

        logger.info("Email successfully read")
        logger.debug(raw_email)

    except Exception as e:
        logger.critical("Failed to read email", exc_info=True)
        return


    # ---------- 2️⃣ PARSE ERROR ---------- #
    logger.info("Parsing error from email")

    parsed = parse_error(raw_email)

    logger.info("Initial parsing completed")
    logger.debug(parsed)


    # ---------- 3️⃣ FETCH SENTRY ISSUE (SAFE) ---------- #
    service_url = parsed.get("service_url")

    if parsed.get("file") is None and service_url and "sentry.io" in service_url:
        try:
            logger.info(f"Fetching Sentry issue from {service_url}")

            issue_text = fetch_sentry_issue(service_url)
            parsed = parse_error(issue_text)

            logger.info("Sentry issue parsed successfully")
            logger.debug(parsed)

        except Exception as e:
            logger.warning("Skipping Sentry fetch (not accessible)", exc_info=True)
    else:
        logger.info("Sentry fetch not required")


    # ---------- 4️⃣ RESOLVE GITHUB REPO ---------- #
    logger.info("Resolving GitHub repository")

    resolver = RepoResolver()
    repo = resolver.resolve(parsed)

    if repo == "UNKNOWN_REPO":
        logger.error("Repository could not be resolved")
        return

    logger.info(f"Resolved repository: {repo}")


    # ---------- 5️⃣ FETCH REPO CODE ---------- #
    try:
        logger.info("Fetching repository code from GitHub")

        fetcher = GitHubFetcher()
        repo_code = fetcher.fetch_repo_code(
            repo,
            parsed.get("file")  # may be None
        )

        if not repo_code.strip():
            logger.warning("No relevant code found in repository")
            return

        logger.info("Repository code fetched successfully")

    except Exception as e:
        logger.error("Failed to fetch repository code", exc_info=True)
        return


    # ---------- 6️⃣ ASK GITHUB COPILOT MODELS ---------- #
    try:
        logger.info("Sending code to GitHub Models (Copilot)")

        ai_response = ask_github_models(parsed, repo_code)

        logger.info("AI fix suggestion received")
        logger.debug(ai_response)

    except Exception as e:
        logger.error("AI analysis failed", exc_info=True)
        return


    # ---------- 7️⃣ NOTIFY MICROSOFT TEAMS ---------- #
    try:
        logger.info("Sending notification to Microsoft Teams")

        notify_teams(
            webhook_url=TEAMS_WEBHOOK_URL,
            title="🚨 AI Agent – Production Error Detected",
            error_summary={
                "message": parsed.get("message"),
                "file": parsed.get("file"),
                "severity": parsed.get("severity"),
                "service_url": parsed.get("service_url"),
                "github_repo": repo
            },
            ai_fix=ai_response
        )

        logger.info("Teams notification sent successfully")

    except Exception as e:
        logger.error("Failed to notify Microsoft Teams", exc_info=True)


    logger.info("✅ AI Agent execution completed successfully")


# ================= ENTRY POINT ================= #

if __name__ == "__main__":
    main()
