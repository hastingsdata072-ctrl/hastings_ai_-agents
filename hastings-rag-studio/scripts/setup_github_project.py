"""
GitHub Projects v2 setup script for Hastings RAG Studio.

Creates a professional project board with milestones, tasks,
and status tracking via the GitHub GraphQL API.
"""

import json
import sys
import urllib.request
import urllib.error

import os

TOKEN = os.environ.get("GITHUB_TOKEN", "")
OWNER = "hastingsdata072-ctrl"
REPO = "hastings-rag-studio"
REPO2 = "hastings_ai_-agents"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def graphql(query: str, variables: dict = None) -> dict:
    """Execute a GitHub GraphQL query."""
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


def get_user_id() -> str:
    data = graphql('query { user(login: "%s") { id } }' % OWNER)
    return data["user"]["id"]


def get_existing_projects(user_id: str) -> list:
    data = graphql("""
    query($login: String!) {
      user(login: $login) {
        projectsV2(first: 20) {
          nodes { id title number }
        }
      }
    }
    """, {"login": OWNER})
    return data["user"]["projectsV2"]["nodes"]


def delete_project(project_id: str) -> None:
    graphql("""
    mutation($id: ID!) {
      deleteProjectV2(input: {projectId: $id}) {
        projectV2 { id }
      }
    }
    """, {"id": project_id})


def create_project(owner_id: str, title: str) -> str:
    data = graphql("""
    mutation($ownerId: ID!, $title: String!) {
      createProjectV2(input: {ownerId: $ownerId, title: $title}) {
        projectV2 { id number url }
      }
    }
    """, {"ownerId": owner_id, "title": title})
    proj = data["createProjectV2"]["projectV2"]
    print(f"  Created project: {proj['url']}")
    return proj["id"]


def get_project_fields(project_id: str) -> dict:
    """Get all fields on a project, return as name->id dict."""
    data = graphql("""
    query($id: ID!) {
      node(id: $id) {
        ... on ProjectV2 {
          fields(first: 20) {
            nodes {
              ... on ProjectV2Field { id name }
              ... on ProjectV2SingleSelectField {
                id name
                options { id name }
              }
            }
          }
        }
      }
    }
    """, {"id": project_id})
    fields = {}
    for f in data["node"]["fields"]["nodes"]:
        fields[f["name"]] = f
    return fields


def update_status_options(project_id: str, field_id: str) -> dict:
    """Get the status field options as name->id dict."""
    fields = get_project_fields(project_id)
    status_field = fields.get("Status", {})
    options = {opt["name"]: opt["id"] for opt in status_field.get("options", [])}
    return options


def add_item(project_id: str, title: str) -> str:
    """Add a draft issue item to a project."""
    data = graphql("""
    mutation($projectId: ID!, $title: String!) {
      addProjectV2DraftIssue(input: {projectId: $projectId, title: $title}) {
        projectItem { id }
      }
    }
    """, {"projectId": project_id, "title": title})
    return data["addProjectV2DraftIssue"]["projectItem"]["id"]


def set_item_status(project_id: str, item_id: str, field_id: str, option_id: str) -> None:
    """Set the Status field on a project item."""
    graphql("""
    mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $projectId,
        itemId: $itemId,
        fieldId: $fieldId,
        value: { singleSelectOptionId: $optionId }
      }) {
        projectV2Item { id }
      }
    }
    """, {
        "projectId": project_id,
        "itemId": item_id,
        "fieldId": field_id,
        "optionId": option_id,
    })


def link_repo_to_project(project_id: str) -> None:
    """Link the repository to the project."""
    # Get repo ID
    data = graphql("""
    query($owner: String!, $repo: String!) {
      repository(owner: $owner, name: $repo) { id }
    }
    """, {"owner": OWNER, "repo": REPO})
    repo_id = data["repository"]["id"]

    graphql("""
    mutation($projectId: ID!, $repoId: ID!) {
      linkProjectV2ToRepository(input: {projectId: $projectId, repositoryId: $repoId}) {
        repository { name }
      }
    }
    """, {"projectId": project_id, "repoId": repo_id})
    print(f"  Linked repository: {REPO}")


# ── Project content ───────────────────────────────────────────────────────────

DONE_ITEMS = [
    "✅ M1: Project skeleton, virtual environment, requirements.txt",
    "✅ M1: PostgreSQL + pgvector setup with Docker",
    "✅ M1: Database schema — knowledge_bases, documents, chunks, HNSW index",
    "✅ M1: src/config.py — environment variable loader with validation",
    "✅ M1: src/db/connection.py — psycopg v3 connection pool",
    "✅ M1: src/health.py — live component health checks",
    "✅ M1: Streamlit System Status page",
    "✅ M2: Document extraction — PDF (page numbers), DOCX, TXT, Markdown",
    "✅ M2: Text chunking with configurable size and overlap",
    "✅ M2: Batch embedding generation (sentence-transformers all-MiniLM-L6-v2)",
    "✅ M2: Knowledge base CRUD — create, list, delete",
    "✅ M2: Document upload, duplicate detection (SHA-256), deletion",
    "✅ M2: Vector similarity search (cosine, pgvector)",
    "✅ M2: Groq answer generation with [S1][S2] citations",
    "✅ M2: Chat interface with sources and retrieved passages",
    "✅ M3: BM25 keyword search (rank-bm25)",
    "✅ M3: Hybrid retrieval with Reciprocal Rank Fusion (RRF)",
    "✅ M3: Cross-encoder reranking (ms-marco-MiniLM-L-6-v2)",
    "✅ M3: Query rewriting via Groq LLM",
    "✅ M3: Context compression (embedding-based sentence scoring)",
    "✅ M3: Citation verification — flags unsupported statements",
    "✅ M3: RAG Intelligence Lab — 7-step pipeline inspector with latency metrics",
    "✅ M4: Persistent chat history — PostgreSQL conversations + messages tables",
    "✅ M4: Conversation export — Markdown and JSON",
    "✅ M4: Evaluation dashboard — Precision@k, Recall@k, MRR",
    "✅ M4: Model selector — switch Groq models from UI",
    "✅ M4: Settings page — session-level config",
    "✅ M4: Dockerfile — multi-stage production build",
    "✅ M4: Deployed to Render (free tier) + Neon (serverless pgvector)",
    "✅ Repo: Professional README with badges, architecture diagram, setup guide",
    "✅ Repo: MIT LICENSE, CONTRIBUTING.md, GitHub issue/PR templates",
]

IN_PROGRESS_ITEMS = [
    "🔄 Monitoring: CloudWatch / Render log alerting",
    "🔄 Performance: Embedding model caching warm-up on startup",
]

BACKLOG_ITEMS = [
    "📋 Feature: User authentication and multi-user support",
    "📋 Feature: OCR for scanned PDFs",
    "📋 Feature: Knowledge graph integration",
    "📋 Feature: Document versioning",
    "📋 Feature: Multilingual retrieval",
    "📋 Feature: Streaming responses (Groq streaming API)",
    "📋 Feature: Custom embedding model support",
    "📋 Feature: Batch question answering / evaluation mode",
    "📋 Feature: API endpoint (FastAPI wrapper)",
    "📋 Feature: S3 document storage for production",
    "📋 Infra: AWS App Runner deployment (when SCP restrictions resolved)",
    "📋 Infra: Custom domain + HTTPS on Render",
    "📋 Infra: Automated CI/CD with GitHub Actions",
]


def main():
    print("🔧 Setting up GitHub Project for Hastings RAG Studio...")
    print()

    # Get user ID
    print("▶ Getting user ID...")
    user_id = get_user_id()
    print(f"  User ID: {user_id}")

    # List existing projects (don't delete them)
    print("\n▶ Checking existing projects...")
    existing = get_existing_projects(user_id)
    for proj in existing:
        print(f"  Existing: {proj['title']} (#{proj['number']})")
    print(f"  Keeping all {len(existing)} existing project(s)")

    # Create new project
    print("\n▶ Creating new project...")
    project_id = create_project(user_id, "Hastings RAG Studio — Roadmap")

    # Link repo
    print("\n▶ Linking repository...")
    link_repo_to_project(project_id)

    # Get status field and options
    print("\n▶ Getting project fields...")
    fields = get_project_fields(project_id)
    status_field = fields.get("Status")
    if not status_field:
        print("  ⚠️  No Status field found — items will be added without status")
        status_field_id = None
        options = {}
    else:
        status_field_id = status_field["id"]
        options = {opt["name"]: opt["id"] for opt in status_field.get("options", [])}
        print(f"  Status options: {list(options.keys())}")

    # Add Done items
    print(f"\n▶ Adding {len(DONE_ITEMS)} completed items...")
    done_option = options.get("Done") or options.get("Closed") or list(options.values())[0] if options else None
    for title in DONE_ITEMS:
        item_id = add_item(project_id, title)
        if status_field_id and done_option:
            set_item_status(project_id, item_id, status_field_id, done_option)
    print(f"  ✅ Added {len(DONE_ITEMS)} done items")

    # Add In Progress items
    print(f"\n▶ Adding {len(IN_PROGRESS_ITEMS)} in-progress items...")
    inprogress_option = options.get("In Progress") or list(options.values())[0] if options else None
    for title in IN_PROGRESS_ITEMS:
        item_id = add_item(project_id, title)
        if status_field_id and inprogress_option:
            set_item_status(project_id, item_id, status_field_id, inprogress_option)
    print(f"  ✅ Added {len(IN_PROGRESS_ITEMS)} in-progress items")

    # Add Backlog items
    print(f"\n▶ Adding {len(BACKLOG_ITEMS)} backlog items...")
    todo_option = options.get("Todo") or options.get("Open") or list(options.values())[0] if options else None
    for title in BACKLOG_ITEMS:
        item_id = add_item(project_id, title)
        if status_field_id and todo_option:
            set_item_status(project_id, item_id, status_field_id, todo_option)
    print(f"  ✅ Added {len(BACKLOG_ITEMS)} backlog items")

    print(f"""
================================================================
  ✅ GitHub Project setup complete!
================================================================

  Project: Hastings RAG Studio — Roadmap
  Items:   {len(DONE_ITEMS)} done / {len(IN_PROGRESS_ITEMS)} in progress / {len(BACKLOG_ITEMS)} backlog

  View at: https://github.com/hastingsdata072-ctrl?tab=projects
================================================================
""")


if __name__ == "__main__":
    main()
