"""
Links the existing Hastings RAG Studio project to the hastings_ai_-agents repo.
Does NOT modify or delete any existing projects.
"""

import json
import sys
import urllib.request

import os

TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER = "hastingsdata072-ctrl"
TARGET_REPO = "hastings_ai_-agents"
PROJECT_TITLE = "Hastings RAG Studio — Roadmap"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def graphql(query: str, variables: dict = None) -> dict:
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=data,
        headers=HEADERS,
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
    if "errors" in result:
        print(f"GraphQL errors: {result['errors']}")
        sys.exit(1)
    return result["data"]


def main():
    # Find the project
    print(f"▶ Finding project '{PROJECT_TITLE}'...")
    data = graphql("""
    query($login: String!) {
      user(login: $login) {
        projectsV2(first: 20) {
          nodes { id title number }
        }
      }
    }
    """, {"login": OWNER})

    projects = data["user"]["projectsV2"]["nodes"]
    project = next((p for p in projects if p["title"] == PROJECT_TITLE), None)

    if not project:
        print(f"  ❌ Project '{PROJECT_TITLE}' not found.")
        print(f"  Available: {[p['title'] for p in projects]}")
        sys.exit(1)

    print(f"  Found: {project['title']} (#{project['number']})")
    project_id = project["id"]

    # Get target repo ID
    print(f"\n▶ Getting repo ID for {TARGET_REPO}...")
    data = graphql("""
    query($owner: String!, $repo: String!) {
      repository(owner: $owner, name: $repo) { id name }
    }
    """, {"owner": OWNER, "repo": TARGET_REPO})
    repo_id = data["repository"]["id"]
    print(f"  Repo ID: {repo_id}")

    # Link project to repo
    print(f"\n▶ Linking project to {TARGET_REPO}...")
    graphql("""
    mutation($projectId: ID!, $repoId: ID!) {
      linkProjectV2ToRepository(input: {
        projectId: $projectId,
        repositoryId: $repoId
      }) {
        repository { name }
      }
    }
    """, {"projectId": project_id, "repoId": repo_id})

    print(f"""
================================================================
  ✅ Done!
================================================================

  Project '{PROJECT_TITLE}' is now linked to:
  - hastings-rag-studio
  - hastings_ai_-agents

  View at: https://github.com/hastingsdata072-ctrl/hastings_ai_-agents/projects
================================================================
""")


if __name__ == "__main__":
    main()
