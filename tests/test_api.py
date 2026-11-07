"""API tests against a throwaway copy of the generated SQLite database."""
import pytest
from fastapi.testclient import TestClient

from recon.cli import cmd_generate, cmd_reconcile
from recon import db as recon_db
from recon.export import read_tables


@pytest.fixture(scope="module")
def client(tmp_path_factory, monkeypatch_module):
    base = tmp_path_factory.mktemp("apidata") / "starter"
    cmd_generate("starter", 20261022, base, sql=False)
    cmd_reconcile(base)
    t = read_tables(base / "input")
    t.update(read_tables(base / "output"))
    recon_db._load_sqlite(t, base / "recon.sqlite")
    from api.db import DB
    from api.main import app  # loads .env - so unset DATABASE_URL *after* import: tests never touch a real DB

    monkeypatch_module.setenv("RECON_DATA_DIR", str(base))
    monkeypatch_module.delenv("DATABASE_URL", raising=False)
    app.state.db = DB()
    return TestClient(app)


@pytest.fixture(scope="module")
def monkeypatch_module():
    mp = pytest.MonkeyPatch()
    yield mp
    mp.undo()


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_summary_counts(client):
    s = client.get("/api/summary").json()
    assert s["counts"]["payment_orders"] == 5000
    assert sum(r["n"] for r in s["exceptions_by_status"]) == 190


def test_exception_filters_and_paging(client):
    r = client.get("/api/exceptions", params={"type": "CURRENCY_MISMATCH"}).json()
    assert r["total"] == 3 and all(x["exception_type"] == "CURRENCY_MISMATCH" for x in r["items"])
    page = client.get("/api/exceptions", params={"limit": 10, "offset": 10}).json()
    assert len(page["items"]) == 10


def _open(client, owner):
    items = client.get("/api/exceptions", params={"owner": owner, "status": "OPEN,IN_REVIEW,ESCALATED"}).json()["items"]
    assert items, f"no open {owner} exceptions in fixture"
    return items[0]


def test_workflow_appends_history_and_resolution(client):
    x = _open(client, "OPS_ANALYST")
    before = client.get(f"/api/exceptions/{x['exception_id']}").json()
    if before["status"] == "OPEN":
        client.post(f"/api/exceptions/{x['exception_id']}/actions", json={"action": "START_REVIEW", "actor_role": "OPS_ANALYST"})
    after = client.post(f"/api/exceptions/{x['exception_id']}/actions",
                        json={"action": "RESOLVE", "actor_role": "OPS_ANALYST", "notes": "verified"}).json()
    assert after["status"] == "RESOLVED"
    assert len(after["history"]) > len(before["history"])
    assert [h["history_id"] for h in after["history"][: len(before["history"])]] == [h["history_id"] for h in before["history"]]
    assert after["resolution"]["notes"] == "verified"


def test_illegal_transition_rejected(client):
    done = client.get("/api/exceptions", params={"status": "RESOLVED", "limit": 1}).json()["items"][0]
    r = client.post(f"/api/exceptions/{done['exception_id']}/actions", json={"action": "RESOLVE", "actor_role": "OPS_ANALYST"})
    assert r.status_code == 409


def test_segregation_of_duties(client):
    x = _open(client, "RISK_REVIEWER")
    r = client.post(f"/api/exceptions/{x['exception_id']}/actions", json={"action": "RESOLVE", "actor_role": "OPS_ANALYST"})
    assert r.status_code == 403
    ok = client.post(f"/api/exceptions/{x['exception_id']}/actions", json={"action": "RESOLVE", "actor_role": "RISK_REVIEWER"})
    assert ok.status_code == 200 and ok.json()["status"] == "RESOLVED"


def test_payment_timeline_and_trace(client):
    pid = client.get("/api/payments", params={"flagged": True}).json()[0]["payment_id"]
    p = client.get(f"/api/payments/{pid}").json()
    assert p["order"]["payment_id"] == pid and p["status_history"] and p["exceptions"]
    t = client.get("/api/trace/SET-2026-000001").json()
    assert t["record"]["batch_id"] == "SET-2026-000001" and t["matches"]


def test_unknown_ids(client):
    assert client.get("/api/trace/NOPE-1").status_code == 400
    assert client.get("/api/payments/PAY-2026-99999999").status_code == 404
