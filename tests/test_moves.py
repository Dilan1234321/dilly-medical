"""Moves metering: caps, 402 shape, bucket rotation, plan tiers."""
from datetime import datetime, timedelta, timezone

from api.database import get_db
from api.moves import get_plan_limit, reset_key_for_plan, spend_move, usage_summary


def test_starter_caps_at_five_with_402(auth):
    client, headers, email = auth
    for i in range(5):
        r = client.post("/readiness/read", headers=headers)
        assert r.status_code == 200, r.text
    r = client.post("/readiness/read", headers=headers)
    assert r.status_code == 402
    detail = r.json()["detail"]
    assert detail["feature"] == "readiness_read"
    assert "message" in detail  # mobile paywall reads this


def test_moves_shared_across_features(auth):
    client, headers, email = auth
    for _ in range(4):
        assert client.post("/readiness/read", headers=headers).status_code == 200
    # 5th move via a DIFFERENT feature still spends from the same pool
    assert client.post("/schools/harvard/scout", headers=headers).status_code == 200
    r = client.post("/readiness/read", headers=headers)
    assert r.status_code == 402


def test_usage_endpoint(auth):
    client, headers, email = auth
    client.post("/readiness/read", headers=headers)
    r = client.get("/moves/usage", headers=headers)
    body = r.json()
    assert body["plan"] == "starter"
    assert body["limit"] == 5
    assert body["used"] == 1
    assert body["remaining"] == 4


def test_pro_is_uncapped(auth):
    client, headers, email = auth
    client.post("/subscription/set-plan", json={"plan": "pro"}, headers=headers)
    for _ in range(8):
        assert client.post("/readiness/read", headers=headers).status_code == 200
    assert usage_summary(email)["remaining"] == -1


def test_weekly_bucket_rotates(auth):
    client, headers, email = auth
    for _ in range(5):
        spend_move(email, "test")
    # Simulate signup 8 days ago -> current week bucket differs from stored one
    with get_db() as conn:
        past = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
        conn.execute("UPDATE users SET created_at=? WHERE email=?", (past, email))
    # stored key was acctW0 (computed when created_at was 'now'); now it's acctW1
    assert reset_key_for_plan("starter", email) == "acctW1"
    assert spend_move(email, "test") == 1  # reset, not 402


def test_dilly_tier_is_monthly_120(auth):
    client, headers, email = auth
    client.post("/subscription/set-plan", json={"plan": "dilly"}, headers=headers)
    assert get_plan_limit("dilly") == 120
    assert reset_key_for_plan("dilly", email).startswith("acctM")


def test_cancel_clears_plan_and_subscribed(auth):
    client, headers, email = auth
    client.post("/subscription/set-plan", json={"plan": "pro"}, headers=headers)
    client.post("/subscription/cancel", headers=headers)
    r = client.get("/auth/me", headers=headers).json()
    assert r["plan"] == "starter"
    assert r["subscribed"] == 0
