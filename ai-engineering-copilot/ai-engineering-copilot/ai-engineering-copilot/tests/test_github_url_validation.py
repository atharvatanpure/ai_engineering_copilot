import pytest

from utils.security import InvalidGitHubURLError, parse_github_url


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/tiangolo/fastapi", ("tiangolo", "fastapi")),
        ("https://github.com/tiangolo/fastapi/", ("tiangolo", "fastapi")),
        ("https://github.com/tiangolo/fastapi.git", ("tiangolo", "fastapi")),
        ("http://github.com/vercel/next.js", ("vercel", "next.js")),
    ],
)
def test_parse_valid_github_urls(url, expected):
    assert parse_github_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not a url",
        "https://gitlab.com/owner/repo",
        "https://github.com/owner-only",
        "ftp://github.com/owner/repo",
    ],
)
def test_parse_invalid_github_urls(url):
    with pytest.raises(InvalidGitHubURLError):
        parse_github_url(url)
