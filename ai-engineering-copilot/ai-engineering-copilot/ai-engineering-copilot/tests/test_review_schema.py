import pytest
from pydantic import ValidationError

from database.schemas import ReviewIssue, ReviewResponse


def test_review_issue_accepts_valid_payload():
    issue = ReviewIssue(
        severity="high",
        category="security",
        file="auth.py",
        line=42,
        title="Hardcoded secret",
        description="A secret key is hardcoded in the source.",
        recommendation="Move the secret to an environment variable.",
    )
    assert issue.severity == "high"


def test_review_issue_rejects_invalid_severity():
    with pytest.raises(ValidationError):
        ReviewIssue(
            severity="catastrophic",  # not a valid enum value
            category="bug",
            file=None,
            line=None,
            title="x",
            description="x",
            recommendation="x",
        )


def test_review_issue_rejects_invalid_category():
    with pytest.raises(ValidationError):
        ReviewIssue(
            severity="low",
            category="not_a_category",
            file=None,
            line=None,
            title="x",
            description="x",
            recommendation="x",
        )


def test_review_response_allows_empty_issue_list():
    response = ReviewResponse(id="abc", summary="No issues found.", issues=[])
    assert response.issues == []
