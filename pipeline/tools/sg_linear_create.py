from __future__ import annotations
import httpx

_MUTATION = """
mutation CreateIssue($title: String!, $description: String, $teamId: String!) {
  issueCreate(input: {title: $title, description: $description, teamId: $teamId}) {
    success
    issue { url }
  }
}
"""


def create_linear_issue(title: str, description: str, team_id: str, api_key: str) -> str:
    try:
        response = httpx.post(
            "https://api.linear.app/graphql",
            json={"query": _MUTATION, "variables": {"title": title, "description": description, "teamId": team_id}},
            headers={"Authorization": api_key},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        # GraphQL always returns HTTP 200 — check the errors array explicitly
        if "errors" in data:
            messages = "; ".join(e.get("message", str(e)) for e in data["errors"])
            raise RuntimeError(f"Linear GraphQL error: {messages}")

        issue_create = (data.get("data") or {}).get("issueCreate") or {}
        if not issue_create.get("success"):
            raise RuntimeError("Linear issueCreate returned success=false")

        issue = issue_create.get("issue") or {}
        url = issue.get("url")
        if not url:
            raise RuntimeError("Linear issue created but URL was not returned")

        return url
    except (httpx.TimeoutException, httpx.NetworkError) as exc:
        raise RuntimeError(f"create_linear_issue network error: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"Linear API returned HTTP {exc.response.status_code}: {exc.response.text[:200]}") from exc
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"create_linear_issue failed: {exc}") from exc
