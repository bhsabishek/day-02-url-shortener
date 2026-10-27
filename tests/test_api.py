import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    return app.test_client()


def shorten(client, url="https://example.com/some/long/path"):
    return client.post("/shorten", json={"url": url})


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


def test_shorten_returns_code(client):
    res = shorten(client)
    assert res.status_code == 201
    body = res.get_json()
    assert len(body["code"]) == 6
    assert body["url"] == "https://example.com/some/long/path"


@pytest.mark.parametrize(
    "bad",
    ["", "   ", "not a url", "javascript:alert(1)", "ftp://example.com/file"],
)
def test_shorten_rejects_invalid_urls(client, bad):
    assert shorten(client, bad).status_code == 400


def test_shorten_rejects_missing_url(client):
    assert client.post("/shorten", json={}).status_code == 400


def test_redirect_is_temporary(client):
    code = shorten(client).get_json()["code"]
    res = client.get(f"/{code}")
    assert res.status_code == 302
    assert res.headers["Location"] == "https://example.com/some/long/path"


def test_unknown_code_redirect_is_404(client):
    assert client.get("/nope123").status_code == 404


def test_hits_are_counted(client):
    code = shorten(client).get_json()["code"]
    client.get(f"/{code}")
    client.get(f"/{code}")
    stats = client.get(f"/stats/{code}").get_json()
    assert stats["hits"] == 2


def test_unknown_code_stats_is_404(client):
    assert client.get("/stats/nope123").status_code == 404


def test_restart_does_not_create_duplicate_codes(tmp_path):
    """Two app instances on the same database file (a restart) must keep working."""
    db = str(tmp_path / "persist.db")
    first = create_app(db_path=db).test_client()
    code_a = first.post("/shorten", json={"url": "https://a.example.com"}).get_json()["code"]

    second = create_app(db_path=db).test_client()
    res = second.post("/shorten", json={"url": "https://b.example.com"})
    assert res.status_code == 201
    assert res.get_json()["code"] != code_a
