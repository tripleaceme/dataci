"""Post or update the DaterCI report as a PR comment."""

from __future__ import annotations

from github import Github
from github.PullRequest import PullRequest

from src.report.composer import COMMENT_MARKER


def get_pull_request(token: str, repo_name: str, pr_number: int) -> PullRequest:
    """Get the pull request object."""
    gh = Github(token)
    repo = gh.get_repo(repo_name)
    return repo.get_pull(pr_number)


def post_or_update_comment(pr: PullRequest, body: str) -> None:
    """Post a new comment or update the existing DaterCI comment.

    Uses the COMMENT_MARKER to find and update previous reports,
    so we don't spam the PR with multiple comments on re-runs.
    """
    for comment in pr.get_issue_comments():
        if COMMENT_MARKER in comment.body:
            comment.edit(body)
            print(f"Updated existing DaterCI comment (id={comment.id})")
            return

    pr.create_issue_comment(body)
    print("Posted new DaterCI comment")
