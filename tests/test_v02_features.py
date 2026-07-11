"""v0.2 feature coverage: interview, secondaries, crawler, voice, health."""
from unittest.mock import patch

from api.school_fit import load_schools


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["db"] in ("sqlite", "postgres")


def test_school_count_at_least_sixty():
    schools = load_schools()["schools"]
    assert len(schools) >= 60
    ids = [s["id"] for s in schools]
    assert len(ids) == len(set(ids)), "duplicate school ids"


def test_interview_session_and_feedback(auth):
    client, headers, _ = auth
    r = client.post("/interview/session", json={"count": 2}, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "session_id" in data
    assert len(data["stations"]) == 2

    r2 = client.post(
        "/interview/feedback",
        json={
            "session_id": data["session_id"],
            "station_index": 0,
            "answer": "I would first listen to the patient and acknowledge their concern before involving the care team.",
        },
        headers=headers,
    )
    assert r2.status_code == 200
    fb = r2.json()["feedback"]
    assert fb["rating"] in ("strong", "good", "needs_work", "weak")
    assert "strengths" in fb
    assert "improvements" in fb


def test_secondaries_prompts_and_craft(auth):
    client, headers, _ = auth
    r = client.get("/secondaries/prompts", headers=headers)
    assert r.status_code == 200
    assert len(r.json()["generic"]) >= 1

    client.post(
        "/hours",
        json={
            "category": "clinical_volunteer",
            "hours": 4,
            "org": "City Hospital",
            "role": "Volunteer",
            "reflection": "A patient thanked me for holding the door during a rough morning.",
        },
        headers=headers,
    )
    prompt = r.json()["generic"][0]
    r2 = client.post(
        "/secondaries/craft",
        json={
            "prompt_id": prompt["id"],
            "prompt_text": prompt["text"],
            "char_limit": 2500,
        },
        headers=headers,
    )
    assert r2.status_code == 200
    out = r2.json()
    assert out["char_count"] > 0
    assert out["limit"] == 2500


def test_voice_transcript_on_hours(auth):
    client, headers, _ = auth
    r = client.post(
        "/hours",
        json={
            "category": "shadowing",
            "hours": 3,
            "org": "Family Medicine Clinic",
            "role": "Shadow",
            "voice_transcript": "The physician explained how she builds trust with nervous patients.",
        },
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["captured_reflection"] is True


def test_crawler_refresh_dev(client):
    with patch("api.crawler.opportunities._fetch", return_value="<rss></rss>"):
        r = client.post("/cron/refresh-opportunities")
    assert r.status_code == 200
    body = r.json()
    assert "sources" in body or "total_upserted" in body
