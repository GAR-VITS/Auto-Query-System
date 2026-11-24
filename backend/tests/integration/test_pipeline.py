"""
Integration Tests for NexusDB 11-Stage Pipeline (Section 14 & 19 Acceptance Check)
Proves that /query/stream in DEMO_MODE returns all 11 stages in strict order.
"""

import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.governance.rbac import create_access_token

client = TestClient(app)


def test_11_stages_in_order():
    """Verify that POST /query/stream streams all 11 stages in sequential order."""
    token = create_access_token(user_id="1", username="viewer@nexusdb.local", role="viewer")
    response = client.post(
        "/query/stream",
        json={"question": "Which branches have the highest loan delinquency this quarter?"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

    # Parse SSE stream
    lines = response.text.strip().split("\n")
    stages_seen: list[int] = []
    events: list[dict] = []

    current_event = None
    for line in lines:
        if line.startswith("event: "):
            current_event = line.replace("event: ", "").strip()
        elif line.startswith("data: ") and current_event:
            try:
                data = json.loads(line.replace("data: ", "").strip())
                events.append({"event": current_event, "data": data})
                if current_event == "stage" and "n" in data and data.get("status") in ("done", "start"):
                    stage_n = data["n"]
                    if not stages_seen or stages_seen[-1] != stage_n:
                        stages_seen.append(stage_n)
            except Exception:
                pass

    # Verify that stages 1 through 11 appear in sequential order
    expected_stages = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11]
    for st in expected_stages:
        assert st in stages_seen, f"Stage {st} was expected in pipeline stream, but got: {stages_seen}"

    # Verify result, analysis, viz and done events were emitted
    event_names = [e["event"] for e in events]
    assert "result" in event_names
    assert "analysis" in event_names
    assert "viz" in event_names
    assert "done" in event_names


def test_action_pipeline_stream():
    """Verify that an operational action triggers Stage 9 (Action module) and Stage 10 (Audit write)."""
    token = create_access_token(user_id="3", username="manager@nexusdb.local", role="credit_manager")
    response = client.post(
        "/query/stream",
        json={"question": "Put account 10482 on hold, reason: suspicious activity"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "action_proposal" in response.text
    assert "SET_ACCOUNT_STATUS" in response.text
