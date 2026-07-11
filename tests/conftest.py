import os
import sys
import tempfile

# Must run BEFORE any api import: point the store at a temp DB, force dev
# mode, and make sure no LLM key leaks in (tests exercise fallbacks).
_TMP = tempfile.mkdtemp(prefix="dilly_med_test_")
os.environ["DILLY_MED_DB"] = os.path.join(_TMP, "test.db")
os.environ["DILLY_MED_DEV"] = "1"
os.environ.pop("ANTHROPIC_API_KEY", None)

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient

from api.database import get_db, init_db
from api.main import app


@pytest.fixture()
def client():
    init_db()
    # Wipe all tables between tests so each test is hermetic.
    with get_db() as conn:
        for table in ("users", "sessions", "auth_codes", "facts", "hours_log",
                      "school_list", "crafts", "readiness_reads", "plan_items"):
            conn.execute(f"DELETE FROM {table}")
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth(client):
    """Signed-in starter user. Returns (client, headers, email)."""
    email = "student@ut.edu"
    r = client.post("/auth/send-code", json={"email": email})
    code = r.json()["dev_code"]
    r = client.post("/auth/verify-code", json={"email": email, "code": code})
    token = r.json()["token"]
    return client, {"Authorization": f"Bearer {token}"}, email
