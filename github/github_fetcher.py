import os
import subprocess
from utils.logger import get_logger

logger = get_logger("github_fetcher")


class GitHubFetcher:
    def fetch_repo_code(self, repo, file_path=None):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GITHUB_TOKEN environment variable is required")

        repo_url = f"https://{token}:x-oauth-basic@github.com/{repo}.git"
        local_path = f"local_repos/{repo.replace('/', '_')}"

        if not os.path.exists(local_path):
            logger.info(f"Cloning {repo}")
            subprocess.run(["git", "clone", "--depth", "1", repo_url, local_path], check=True)
        else:
            logger.info(f"Pulling latest for {repo}")
            subprocess.run(["git", "-C", local_path, "pull"], check=True)

        if file_path:
            full_path = os.path.join(local_path, file_path)
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            return ""

        collected = []
        for root, _, files in os.walk(local_path):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as fh:
                        collected.append(f"\n# {os.path.relpath(os.path.join(root, f), local_path)}\n{fh.read()}")

        return "\n".join(collected)
