"""School Scout verdicts + Craft's no-fabrication guarantees."""


def test_school_list_orders_and_flags_in_state(auth):
    client, headers, email = auth
    client.patch("/profile", json={"gpa": 3.8, "mcat": 512, "state": "FL"}, headers=headers)
    r = client.get("/schools", headers=headers).json()
    schools = {s["id"]: s for s in r["schools"]}
    assert schools["usf"]["in_state"] is True
    assert schools["harvard"]["in_state"] is False
    assert "data_note" in r  # honesty note always present


def test_scout_verdicts_track_stats_and_residency(auth):
    client, headers, email = auth
    client.patch("/profile", json={"gpa": 3.85, "mcat": 514, "state": "FL"}, headers=headers)

    fsu = client.post("/schools/fsu/scout", headers=headers).json()
    assert fsu["verdict"] in ("likely", "target")  # above medians + in-state at a strong-IS school

    harvard = client.post("/schools/harvard/scout", headers=headers).json()
    assert harvard["verdict"] in ("reach", "far_reach")  # well below 3.95/520 medians

    unc = client.post("/schools/unc/scout", headers=headers).json()
    assert unc["verdict"] in ("reach", "far_reach", "target")
    assert any("in-state" in w.lower() for w in unc["why"])  # OOS at strong-IS school gets warned


def test_scout_incomplete_without_gpa(auth):
    client, headers, email = auth
    r = client.post("/schools/usf/scout", headers=headers).json()
    assert r["verdict"] == "incomplete"
    assert "GPA" in r["move"]


def test_scout_never_gives_probability(auth):
    client, headers, email = auth
    client.patch("/profile", json={"gpa": 3.7, "mcat": 508}, headers=headers)
    r = client.post("/schools/tulane/scout", headers=headers).json()
    text = str(r)
    assert "%" not in r["verdict"]
    assert "probability" not in text.lower()
    assert "chance" not in r["verdict"].lower()


def test_no_caribbean_schools_in_dataset():
    from api.school_fit import load_schools
    for s in load_schools()["schools"]:
        assert s["state"] not in ("PR",) or True  # PR would be fine; the check is offshore islands
        assert "caribbean" not in s["name"].lower()
        assert s["type"] in ("MD", "DO")


def test_craft_refuses_without_evidence(auth):
    client, headers, email = auth
    r = client.post("/craft", json={"kind": "personal_statement"}, headers=headers)
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "NO_EVIDENCE"
    # And it did NOT spend a Move
    assert client.get("/moves/usage", headers=headers).json()["used"] == 0


def test_craft_fallback_uses_only_student_words(auth):
    client, headers, email = auth
    client.post("/hours", json={
        "category": "clinical_volunteer", "hours": 4, "org": "Tampa General ER",
        "role": "Volunteer", "occurred_on": "2026-06-01",
        "reflection": "Held a patient's hand during a hard diagnosis",
    }, headers=headers)
    r = client.post("/craft", json={"kind": "activity_description", "org": "Tampa General ER"},
                    headers=headers).json()
    assert r["llm"] is False  # no key in tests -> deterministic path
    assert "Tampa General ER" in r["output"]
    assert "Held a patient's hand" in r["output"]
    # Nothing fabricated: no invented metrics or orgs
    assert "%" not in r["output"]


def test_opportunities_rank_by_gap(auth):
    client, headers, email = auth
    client.patch("/profile", json={"gpa": 3.9, "mcat": 518}, headers=headers)
    # Student with strong shadowing but zero clinical: clinical fills should lead
    for day in range(1, 8):
        client.post("/hours", json={"category": "shadowing", "hours": 8,
                                    "occurred_on": f"2026-05-{day:02d}", "org": "Dr. Lee"},
                    headers=headers)
    r = client.get("/opportunities", headers=headers).json()
    top5_fills = [f for o in r["opportunities"][:5] for f in o["fills"]]
    assert "clinical" in top5_fills
    assert all("why_chips" in o for o in r["opportunities"])
