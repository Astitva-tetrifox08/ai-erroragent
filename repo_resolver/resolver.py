import os
import requests
from urllib.parse import urlparse
from utils.logger import get_logger

logger = get_logger("resolver")


class RepoResolver:
    def __init__(self):
        self.org = os.getenv("GITHUB_ORG")
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.org:
            raise RuntimeError("GITHUB_ORG environment variable is required")
        if not self.token:
            raise RuntimeError("GITHUB_TOKEN environment variable is required")
        self.repos = self._fetch_org_repos()

    def _fetch_org_repos(self):
        repos = []
        page = 1
        while True:
            resp = requests.get(
                f"https://api.github.com/orgs/{self.org}/repos",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json",
                },
                params={"per_page": 100, "page": page},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            repos.extend([r["name"] for r in data if not r.get("archived")])
            page += 1
        logger.info(f"Loaded {len(repos)} repos from '{self.org}'")
        return repos

    def resolve(self, parsed):
        if parsed.get("github_link"):
            return parsed["github_link"].replace("https://github.com/", "")

        project = (parsed.get("project_name") or "").lower()

        # Exact match
        for repo in self.repos:
            if repo.lower() == project:
                return f"{self.org}/{repo}"

        # Partial match
        for repo in self.repos:
            if repo.lower() in project or project in repo.lower():
                return f"{self.org}/{repo}"

        # Service URL fallback
        if parsed.get("service_url"):
            domain = urlparse(parsed["service_url"]).netloc.lower()
            for repo in self.repos:
                if repo.lower() in domain:
                    return f"{self.org}/{repo}"

        # File path search - find which repo contains the exception file
        file_path = parsed.get("file")
        if file_path:
            filename = file_path.split("/")[-1]
            repo = self._search_file_in_org(filename)
            if repo:
                return repo

        logger.warning(f"No match for project: {project}")
        return "UNKNOWN_REPO"

    def _search_file_in_org(self, filename):
        """Search GitHub for which repo in the org contains this file."""
        try:
            resp = requests.get(
                "https://api.github.com/search/code",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json",
                },
                params={"q": f"filename:{filename} org:{self.org}"},
                timeout=10,
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            if items:
                repo_name = items[0]["repository"]["full_name"]
                logger.info(f"Found '{filename}' in repo: {repo_name}")
                return repo_name
        except Exception:
            logger.warning(f"GitHub code search failed for: {filename}", exc_info=True)
        return None
