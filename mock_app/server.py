"""
Mock next-generation Supply Chain Planning (SCP) SaaS application.

Synthetic re-creation of planner workflows: demand workbench with forecast
overrides (frozen horizon, reason codes), inventory policy calculation
(safety stock / reorder point), replenishment recommendations with MOQ
rounding and approval, and what-if scenario planning.
No proprietary code, algorithms or data.
"""
from __future__ import annotations

import copy
import itertools
import math
from datetime import datetime, timezone
from pathlib import Path

from mock_app.core import ApiError, App, require

app = App(Path(__file__).parent / "static")

WEEKS = [f"W{n}" for n in range(1, 9)]
FROZEN_WEEKS = 2                   # W1-W2 cannot be overridden
REASON_THRESHOLD = 0.20            # overrides > ±20 % vs statistical need a reason code
MAX_OVERRIDE = 1_000_000
REASON_CODES = ["PROMOTION", "NEW_CUSTOMER", "SEASONALITY", "MARKET_INTEL", "SUPPLY_CONSTRAINT"]
Z_SCORES = {90: 1.28, 95: 1.65, 98: 2.05, 99: 2.33}

USERS_SEED = {
    "planner": {"password": "Plan@123", "display_name": "Demand Planner", "role": "PLANNER"},
    "viewer": {"password": "Plan@123", "display_name": "Read-only Viewer", "role": "VIEWER"},
}

ITEMS_SEED = [
    {"sku": "SKU-1001", "description": "Organic Oat Milk 1L", "location": "DC-PUNE", "stat": [520, 540, 560, 580, 600, 610, 590, 570]},
    {"sku": "SKU-1002", "description": "Almond Butter 350g", "location": "DC-PUNE", "stat": [210, 205, 220, 230, 240, 235, 225, 215]},
    {"sku": "SKU-2001", "description": "Steel Water Bottle", "location": "DC-MUMBAI", "stat": [80, 85, 90, 95, 100, 120, 140, 160]},
    {"sku": "SKU-3001", "description": "Bamboo Toothbrush 4pk", "location": "DC-MUMBAI", "stat": [1200, 1180, 1220, 1250, 1300, 1280, 1260, 1240]},
]

RECS_SEED = [
    {"sku": "SKU-1001", "supplier": "GreenFarm Dairy", "required_qty": 1130, "moq": 250, "unit_cost": 1.85, "due": "W3"},
    {"sku": "SKU-1002", "supplier": "NutriSpread Ltd", "required_qty": 430, "moq": 100, "unit_cost": 4.20, "due": "W3"},
    {"sku": "SKU-2001", "supplier": "Metalware Co", "required_qty": 95, "moq": 48, "unit_cost": 6.75, "due": "W4"},
    {"sku": "SKU-3001", "supplier": "EcoBrush Exports", "required_qty": 2500, "moq": 500, "unit_cost": 2.10, "due": "W4"},
]

STATE: dict = {}
_ids = itertools.count(1)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def round_up_to_moq(qty: int, moq: int) -> int:
    return int(math.ceil(qty / moq) * moq)


def reset() -> None:
    global _ids
    _ids = itertools.count(500)
    app.revoke_all_tokens()
    STATE.clear()
    STATE["users"] = copy.deepcopy(USERS_SEED)
    STATE["items"] = {}
    for item in ITEMS_SEED:
        key = f"{item['sku']}@{item['location']}"
        STATE["items"][key] = {"key": key, "sku": item["sku"], "description": item["description"],
                               "location": item["location"],
                               "statistical": dict(zip(WEEKS, item["stat"])),
                               "overrides": {}, "audit": []}
    STATE["recs"] = {}
    for r in RECS_SEED:
        rid = next(_ids)
        qty = round_up_to_moq(r["required_qty"], r["moq"])
        STATE["recs"][rid] = {"id": rid, **r, "recommended_qty": qty, "value": round(qty * r["unit_cost"], 2),
                              "status": "PROPOSED", "reason": None}
    STATE["scenarios"] = {}


def item_view(item: dict) -> dict:
    final = {w: item["overrides"].get(w, {}).get("qty", item["statistical"][w]) for w in WEEKS}
    return {**{k: v for k, v in item.items() if k != "overrides"},
            "overrides": {w: o for w, o in item["overrides"].items()},
            "final": final, "total_statistical": sum(item["statistical"].values()),
            "total_final": sum(final.values())}


def planner_only(req):
    if req.user["role"] != "PLANNER":
        raise ApiError(403, "Read-only users cannot change plans")


# --------------------------------------------------------------------------- hooks / auth
@app.route("POST", "/api/test/reset", auth=False)
def _reset(req):
    reset()
    return {"status": "reset"}


@app.route("POST", "/api/auth/login", auth=False)
def login(req):
    username = require(req.body, "username", "Username")
    password = require(req.body, "password", "Password", strip=False)
    user = STATE["users"].get(username)
    if not user or user["password"] != password:
        raise ApiError(401, "Invalid username or password")
    profile = {"username": username, "display_name": user["display_name"], "role": user["role"]}
    return {"token": app.issue_token(profile), "user": profile}


@app.route("GET", "/api/meta")
def meta(req):
    return {"weeks": WEEKS, "frozen_weeks": WEEKS[:FROZEN_WEEKS], "reason_codes": REASON_CODES,
            "reason_threshold_pct": int(REASON_THRESHOLD * 100), "service_levels": list(Z_SCORES)}


# --------------------------------------------------------------------------- demand workbench
@app.route("GET", "/api/demand")
def demand(req):
    loc = req.query.get("location")
    items = [item_view(i) for i in STATE["items"].values() if not loc or i["location"] == loc]
    return {"weeks": WEEKS, "items": items,
            "grand_total_final": sum(i["total_final"] for i in items)}


@app.route("PUT", r"/api/demand/(?P<key>[^/]+)/override")
def set_override(req):
    planner_only(req)
    item = STATE["items"].get(req.params["key"])
    if not item:
        raise ApiError(404, "Item-location not found")
    week = require(req.body, "week", "Week")
    if week not in WEEKS:
        raise ApiError(400, "Unknown planning bucket", field="week")
    if week in WEEKS[:FROZEN_WEEKS]:
        raise ApiError(422, f"{week} is inside the frozen horizon and cannot be changed", field="week")
    qty = req.body.get("qty")
    if qty is None:                                  # clearing an override
        item["overrides"].pop(week, None)
        item["audit"].append({"week": week, "action": "CLEARED", "by": req.user["username"], "at": now()})
        return item_view(item)
    if not isinstance(qty, int) or isinstance(qty, bool) or qty < 0 or qty > MAX_OVERRIDE:
        raise ApiError(400, f"Override must be a whole number between 0 and {MAX_OVERRIDE:,}", field="qty")
    stat = item["statistical"][week]
    change = abs(qty - stat) / stat if stat else 1
    reason = req.body.get("reason")
    if change > REASON_THRESHOLD and not reason:
        raise ApiError(400, f"A reason code is required for changes above {int(REASON_THRESHOLD * 100)}%", field="reason")
    if reason and reason not in REASON_CODES:
        raise ApiError(400, "Unknown reason code", field="reason")
    item["overrides"][week] = {"qty": qty, "reason": reason, "by": req.user["username"]}
    item["audit"].append({"week": week, "action": "OVERRIDE", "from": stat, "to": qty, "reason": reason,
                          "by": req.user["username"], "at": now()})
    return item_view(item)


# --------------------------------------------------------------------------- inventory policy
@app.route("POST", "/api/inventory/policy")
def inventory_policy(req):
    b = req.body
    try:
        avg = float(b.get("avg_daily_demand"))
        sd = float(b.get("demand_std_dev"))
        lt = float(b.get("lead_time_days"))
        sl = int(b.get("service_level"))
    except (TypeError, ValueError):
        raise ApiError(400, "All inputs are required and must be numeric")
    if avg < 0 or sd < 0:
        raise ApiError(400, "Demand inputs cannot be negative", field="avg_daily_demand" if avg < 0 else "demand_std_dev")
    if not 1 <= lt <= 365:
        raise ApiError(400, "Lead time must be between 1 and 365 days", field="lead_time_days")
    if sl not in Z_SCORES:
        raise ApiError(400, "Service level must be one of 90, 95, 98, 99", field="service_level")
    z = Z_SCORES[sl]
    safety_stock = math.ceil(round(z * sd * math.sqrt(lt), 6))
    rop = math.ceil(round(avg * lt + safety_stock, 6))
    return {"z": z, "safety_stock": safety_stock, "reorder_point": rop}


# --------------------------------------------------------------------------- replenishment
@app.route("GET", "/api/replenishment")
def recs(req):
    items = list(STATE["recs"].values())
    status = req.query.get("status")
    if status:
        items = [r for r in items if r["status"] == status.upper()]
    return {"count": len(items), "items": items,
            "approved_value": round(sum(r["value"] for r in STATE["recs"].values() if r["status"] == "APPROVED"), 2)}


def _rec(rid):
    r = STATE["recs"].get(int(rid))
    if not r:
        raise ApiError(404, "Recommendation not found")
    return r


@app.route("PUT", r"/api/replenishment/(?P<rid>\d+)")
def edit_rec(req):
    planner_only(req)
    r = _rec(req.params["rid"])
    if r["status"] != "PROPOSED":
        raise ApiError(409, "Only proposed recommendations can be edited")
    qty = req.body.get("qty")
    if not isinstance(qty, int) or qty < 1:
        raise ApiError(400, "Quantity must be a positive whole number", field="qty")
    if qty % r["moq"]:
        raise ApiError(400, f"Quantity must be a multiple of the MOQ ({r['moq']})", field="qty")
    r["recommended_qty"] = qty
    r["value"] = round(qty * r["unit_cost"], 2)
    return r


@app.route("POST", "/api/replenishment/approve")
def approve(req):
    planner_only(req)
    ids = req.body.get("ids") or []
    if not ids:
        raise ApiError(400, "Select at least one recommendation", field="ids")
    recs_ = [_rec(i) for i in ids]
    for r in recs_:
        if r["status"] != "PROPOSED":
            raise ApiError(409, f"Recommendation {r['id']} is already {r['status'].lower()}")
    for r in recs_:
        r["status"] = "APPROVED"
        r["po_number"] = f"PO-{r['id']:06d}"
    return {"approved": [r["id"] for r in recs_]}


@app.route("POST", r"/api/replenishment/(?P<rid>\d+)/reject")
def reject(req):
    planner_only(req)
    r = _rec(req.params["rid"])
    reason = (req.body.get("reason") or "").strip()
    if len(reason) < 5:
        raise ApiError(400, "Please give a rejection reason (min 5 characters)", field="reason")
    if r["status"] != "PROPOSED":
        raise ApiError(409, f"Recommendation {r['id']} is already {r['status'].lower()}")
    r["status"], r["reason"] = "REJECTED", reason
    return r


# --------------------------------------------------------------------------- scenarios
@app.route("GET", "/api/scenarios")
def list_scenarios(req):
    return {"items": list(STATE["scenarios"].values())}


@app.route("POST", "/api/scenarios")
def create_scenario(req):
    planner_only(req)
    name = require(req.body, "name", "Scenario name")
    uplift = req.body.get("uplift_pct")
    if not isinstance(uplift, (int, float)) or not -50 <= uplift <= 100:
        raise ApiError(400, "Uplift must be between -50% and 100%", field="uplift_pct")
    if any(s["name"].lower() == name.lower() for s in STATE["scenarios"].values()):
        raise ApiError(409, "Scenario name already exists", field="name")
    baseline = sum(item_view(i)["total_final"] for i in STATE["items"].values())
    scenario_total = round(baseline * (1 + uplift / 100))
    sid = next(_ids)
    sc = {"id": sid, "name": name, "uplift_pct": uplift, "baseline_total": baseline,
          "scenario_total": scenario_total, "delta": scenario_total - baseline, "created_at": now()}
    STATE["scenarios"][sid] = sc
    return 201, sc


@app.route("DELETE", r"/api/scenarios/(?P<sid>\d+)")
def delete_scenario(req):
    planner_only(req)
    if STATE["scenarios"].pop(int(req.params["sid"]), None) is None:
        raise ApiError(404, "Scenario not found")
    return {"deleted": int(req.params["sid"])}


def create_server(host: str = "127.0.0.1", port: int = 0):
    reset()
    return app.create_server(host, port)


if __name__ == "__main__":
    srv = create_server("127.0.0.1", 8000)
    print("Mock planning app at http://127.0.0.1:8000  (planner / Plan@123)")
    srv.serve_forever()
