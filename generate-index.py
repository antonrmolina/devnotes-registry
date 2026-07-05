import base64
import json
import os
# registry index generator — force redeploy

import requests
import yaml

REGISTRY_FILE = "devnotes-registry.yml"
OUTPUT_FILE = "devnotes-index.json"
GITHUB_API = "https://api.github.com"

token = os.environ.get("GITHUB_TOKEN")
if token:
    headers = {"Authorization": f"Bearer {token}"}
else:
    print("Running unauthenticated (rate limit: 60 req/hr)")
    headers = {}


def get(url):
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def extract_frontmatter(md_content):
    md_content = md_content.strip()
    if not md_content.startswith("---"):
        return None
    end = md_content.find("\n---", 3)
    if end == -1:
        return None
    return yaml.safe_load(md_content[3:end].strip())


with open(REGISTRY_FILE) as f:
    registry = yaml.safe_load(f)

entries = []
repo_count = 0

for repo_entry in registry["repos"]:
    org = repo_entry["org"]
    repo = repo_entry["repo"]
    repo_count += 1

    contents_url = f"{GITHUB_API}/repos/{org}/{repo}/contents/"
    try:
        items = get(contents_url)
    except requests.HTTPError as e:
        print(f"Warning: could not list {org}/{repo}: {e}")
        continue

    dirs = [item for item in items if item["type"] == "dir"]

    for item in dirs:
        subdir = item["name"]
        md_url = f"{GITHUB_API}/repos/{org}/{repo}/contents/{subdir}/index.md"

        try:
            md_item = get(md_url)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                continue
            print(f"Warning: {subdir}: HTTP error fetching index.md: {e}")
            continue

        try:
            raw = base64.b64decode(md_item["content"]).decode("utf-8")
            fm = extract_frontmatter(raw)
            if fm is None:
                print(f"Warning: {subdir}: no YAML frontmatter found in index.md")
                continue

            thumbnail = fm.get("thumbnail", "")
            entry = {
                "title": fm.get("title", ""),
                "description": fm.get("description", ""),
                "date": str(fm.get("date", "")),
                "authors": fm.get("authors", []),
                "keywords": fm.get("keywords", []),
                "license": fm.get("license", ""),
                "thumbnail": thumbnail,
                "collections": fm.get("collections", []),
                "thumbnail_url": (
                    f"https://raw.githubusercontent.com/{org}/{repo}/main/{subdir}/{thumbnail}"
                    if thumbnail else ""
                ),
                "devnote_url": f"https://{org}.github.io/{repo}/{subdir}/",
                "repo_org": org,
                "repo_name": repo,
                "subdir": subdir,
            }
            entries.append(entry)
        except Exception as e:
            print(f"Warning: {subdir}: parse error: {e}")
            continue

entries.sort(key=lambda e: e["date"], reverse=True)

with open(OUTPUT_FILE, "w") as f:
    json.dump(entries, f, indent=2)

print(f"Found {len(entries)} DevNotes across {repo_count} repos")
print(f"Written to {OUTPUT_FILE}")
