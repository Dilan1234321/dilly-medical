"""Hours ledger (free, never metered) + Readiness Read engine."""


def _log(client, headers, **kw):
    body = {"category": "clinical_volunteer", "hours": 4, "org": "Tampa General ER",
            "role": "Volunteer", "occurred_on": "2026-06-01", "reflection": ""}
    body.update(kw)
    r = client.post("/hours", json=body, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def test_hours_log_and_totals(auth):
    client, headers, email = auth
    _log(client, headers, hours=4)
    _log(client, headers, hours=6, category="clinical_paid", role="Scribe")
    _log(client, headers, hours=3, category="shadowing", org="Dr. Patel Family Medicine")
    r = client.get("/hours", headers=headers).json()
    assert r["clinical_total"] == 10
    assert r["totals"]["shadowing"] == 3
    assert len(r["entries"]) == 3


def test_hours_never_metered(auth):
    client, headers, email = auth
    for _ in range(5):
        client.post("/readiness/read", headers=headers)  # exhaust all Moves
    assert _log(client, headers)["id"]  # logging still works
    assert client.get("/hours", headers=headers).status_code == 200


def test_readiness_bands_move_with_evidence(auth):
    client, headers, email = auth
    client.patch("/profile", json={"gpa": 3.85, "mcat": 514, "gpa_trend": "rising"}, headers=headers)

    r1 = client.post("/readiness/read", headers=headers).json()
    dims1 = {d["dimension"]: d for d in r1["dimensions"]}
    assert dims1["stats"]["band"] == "strong"          # above matriculant avgs
    assert dims1["clinical"]["band"] == "getting_started"  # zero hours
    assert r1["your_open_lane"] in ("clinical", "shadowing", "research_and_service", "story")

    # Log a real clinical base + reflections, read again
    for day in range(1, 9):
        _log(client, headers, hours=8, occurred_on=f"2026-05-{day:02d}",
             reflection=f"Patient moment {day} that stuck with me")
    for day in range(1, 8):
        _log(client, headers, hours=8, occurred_on=f"2026-06-{day:02d}", category="clinical_paid", role="Scribe")

    r2 = client.post("/readiness/read", headers=headers).json()
    dims2 = {d["dimension"]: d for d in r2["dimensions"]}
    assert dims2["clinical"]["band"] in ("on_track", "building")
    assert dims2["story"]["band"] in ("on_track", "building")
    # Evidence cites real hours entries
    assert any("[H" in e for e in dims2["clinical"]["evidence"])


def test_readiness_never_outputs_numeric_verdict(auth):
    client, headers, email = auth
    client.patch("/profile", json={"gpa": 3.5}, headers=headers)
    read = client.post("/readiness/read", headers=headers).json()
    for d in read["dimensions"]:
        assert d["band"] in ("getting_started", "building", "on_track", "strong", "unknown")
        assert "score" not in d


def test_wa_export_groups_activities(auth):
    client, headers, email = auth
    for day in ("2026-01-10", "2026-02-14", "2026-03-20"):
        _log(client, headers, occurred_on=day, reflection=f"reflection on {day}")
    _log(client, headers, org="Moffitt Lab", role="Research Assistant", category="research",
         occurred_on="2026-04-01")
    r = client.get("/hours/export", headers=headers).json()
    assert len(r["activities"]) == 2
    top = r["activities"][0]
    assert top["org"] == "Tampa General ER"
    assert top["total_hours"] == 12
    assert top["first_date"] == "2026-01-10" and top["last_date"] == "2026-03-20"
    assert len(top["reflections"]) == 3
