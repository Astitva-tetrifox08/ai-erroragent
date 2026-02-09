import os
import subprocess

class GitHubFetcher:
    def fetch_repo_code(self, repo, file_path=None):
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("❌ GITHUB_TOKEN environment variable not set")

        repo_url = f"https://{token}:x-oauth-basic@github.com/{repo}.git"
        local_path = f"local_repos/{repo.replace('/', '_')}"

        if not os.path.exists(local_path):
            subprocess.run(
                ["git", "clone", repo_url, local_path],
                check=True
            )
        else:
            subprocess.run(
                ["git", "-C", local_path, "pull"],
                check=True
            )

        # If file is provided, read it
        if file_path:
            full_path = os.path.join(local_path, file_path)
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()

        # Otherwise return repo tree
        collected = []
        for root, _, files in os.walk(local_path):
            for f in files:
                if f.endswith(".py"):
                    with open(os.path.join(root, f), "r", encoding="utf-8", errors="ignore") as fh:
                        collected.append(f"\n# {root}/{f}\n" + fh.read())

        return "\n".join(collected)
