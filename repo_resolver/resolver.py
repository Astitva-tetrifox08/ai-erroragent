import json
from urllib.parse import urlparse

# 🔥 THIS WILL PRINT WHEN FILE IS LOADED

print("🔥 NEW RESOLVER LOADED 🔥")


class RepoResolver:
    def __init__(self):
        with open("repo_resolver/repo_map.json") as f:
            self.map = json.load(f)

    def resolve(self, parsed):

        print("DEBUG project_name:", parsed.get("project_name"))

        # 1. Direct GitHub link
        if parsed.get("github_link"):
            return parsed["github_link"].replace("https://github.com/", "")

        project = (parsed.get("project_name") or "").lower()

        # 2. STRONG MATCH (exact)
        if project in self.map:
            return self.map[project]["repo"]

        # 3. PARTIAL MATCH (contains)
        for key in self.map:
            if key.lower() in project or project in key.lower():
                return self.map[key]["repo"]

        # 4. SERVICE URL fallback
        if parsed.get("service_url"):
            domain = urlparse(parsed["service_url"]).netloc.lower()

            for key in self.map:
                if key.lower() in domain:
                    return self.map[key]["repo"]

        print("DEBUG: No match found for:", project)

        # 🔥 FORCE RETURN (TEMP FIX)
        return "UNKNOWN_REPO"