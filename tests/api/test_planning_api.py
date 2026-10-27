import pytest

from api.planning_client import PlanningClient
from utils.data_loader import cases

OAT = "SKU-1001@DC-PUNE"


@pytest.fixture
def client(api) -> PlanningClient:
    return PlanningClient(api)


@pytest.mark.api
@pytest.mark.smoke
def test_final_forecast_equals_stat_without_overrides(client):
    for item in client.demand().json()["items"]:
        assert item["final"] == item["statistical"]
        assert item["total_final"] == sum(item["statistical"].values())


@pytest.mark.api
@pytest.mark.regression
def test_override_audit_trail(client):
    body = client.override(OAT, "W6", 900, "PROMOTION").json()
    assert body["final"]["W6"] == 900
    entry = body["audit"][-1]
    assert entry | {"at": None} == {"week": "W6", "action": "OVERRIDE", "from": 610, "to": 900,
                                    "reason": "PROMOTION", "by": "planner", "at": None}


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.parametrize("week, qty, reason, status, error", [
    ("W1", 500, None, 422, "W1 is inside the frozen horizon and cannot be changed"),
    ("W9", 500, None, 400, "Unknown planning bucket"),
    ("W4", 580, "BECAUSE", 400, "Unknown reason code"),
    ("W4", True, None, 400, "Override must be a whole number between 0 and 1,000,000"),
], ids=["frozen", "unknown-week", "bad-reason", "boolean-qty"])
def test_override_rules(client, week, qty, reason, status, error):
    resp = client.override(OAT, week, qty, reason)
    assert resp.status == status
    assert resp.json()["error"] == error


@pytest.mark.api
@pytest.mark.regression
def test_override_to_zero_needs_reason(client):
    assert client.override(OAT, "W5", 0).status == 400
    assert client.override(OAT, "W5", 0, "SUPPLY_CONSTRAINT").json()["final"]["W5"] == 0


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize("case", cases("inventory_policy", "policy_cases"))
def test_policy_math(client, case):
    body = client.policy(avg_daily_demand=case["avg"], demand_std_dev=case["std"],
                         lead_time_days=case["lead_time"], service_level=case["service_level"]).json()
    assert body == {"z": case["z"], "safety_stock": case["safety_stock"], "reorder_point": case["reorder_point"]}


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
def test_policy_rejects_unknown_service_level(client):
    resp = client.policy(avg_daily_demand=10, demand_std_dev=2, lead_time_days=5, service_level=97)
    assert resp.json()["field"] == "service_level"


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
def test_cannot_approve_twice(client):
    assert client.approve([500]).ok
    resp = client.approve([500, 501])
    assert resp.status == 409
    assert client.recs("PROPOSED").json()["count"] == 3, "partial approval must not happen"


@pytest.mark.api
@pytest.mark.negative
@pytest.mark.regression
def test_viewer_is_read_only(playwright, base_url):
    ctx = playwright.request.new_context(base_url=base_url)
    token = ctx.post("/api/auth/login", data={"username": "viewer", "password": "Plan@123"}).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert ctx.get("/api/demand", headers=headers).ok
    resp = ctx.put(f"/api/demand/{OAT}/override", data={"week": "W4", "qty": 590}, headers=headers)
    assert resp.status == 403
    ctx.dispose()


@pytest.mark.api
@pytest.mark.regression
def test_scenario_math(client):
    body = client.create_scenario("Down 20", -20).json()
    assert body["baseline_total"] == 17150
    assert body["scenario_total"] == 13720
    assert body["delta"] == -3430
