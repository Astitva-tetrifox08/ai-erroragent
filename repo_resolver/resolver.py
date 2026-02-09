import json
from urllib.parse import urlparse

class RepoResolver:
    def __init__(self):
        with open("repo_resolver/repo_map.json") as f:
            self.map = json.load(f)

    def resolve(self, parsed):
        if parsed.get("github_link"):
            return parsed["github_link"].replace("https://github.com/", "")

        if parsed.get("project_name") and parsed["project_name"] in self.map:
            return self.map[parsed["project_name"]]["repo"]

        if parsed.get("service_url"):
            domain = urlparse(parsed["service_url"]).netloc
            if domain in self.map:
                return self.map[domain]["repo"]

        return "UNKNOWN_REPO"
