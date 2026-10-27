# Supply Chain Planning (Xpression NextGen) — Python + Playwright Automation

![Tests](https://github.com/kpravinsqa/playwright-python-xpression-nextgen/actions/workflows/tests.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue) ![Playwright](https://img.shields.io/badge/playwright-python-2EAD33) ![Domain](https://img.shields.io/badge/domain-Supply%20Chain%20Planning-3b2f80)

UI and API automation for a **next-generation SaaS supply chain planning** application, modelled on the planner
workflows I tested on the **Xpression NextGen** project (Supply Chain Planning domain): the demand workbench with
editable forecast grids, inventory policy (safety stock / reorder point), replenishment recommendations with MOQ
rounding and approvals, and what-if scenario planning.

> **Confidentiality note:** original portfolio project. It contains **no proprietary code, algorithms, data or screens**.
> The planning rules are textbook formulas reproduced in a small mock app (`mock_app/`), so the suite runs anywhere.

## Highlights

* **Editable data-grid automation**: cell-level overrides, frozen-horizon locking, live total recalculation, override highlighting
* **Business-rule boundaries**: ±20 % reason-code threshold (exactly 20 % vs 21 %), uplift −50 % / +100 %, lead time 1 / 365 / 366
* **Calculation verification**: safety stock `ceil(z·σ·√LT)` and ROP `ceil(avg·LT + SS)` across 7 data-driven cases, UI and API
* **Workflow and state**: bulk approval with PO generation, rejection with mandatory reason, atomic approval (no partial commits)
* **Role-based access**: read-only viewer checked in the UI (disabled controls) and the API (`403`)
* **Audit trail** assertions on every forecast override

## Coverage (71 automated checks)

| Suite | Module | Key scenarios |
|---|---|---|
| TS-01 | Login | valid / invalid, password not trimmed, required fields, deep-link redirect |
| TS-02 | Demand workbench | grid totals, frozen W1–W2, override ±threshold, reason codes, invalid values, clear override, location filter, viewer lock |
| TS-03 | Inventory policy | SS / ROP at 90 / 95 / 98 / 99 % service level, zero variability, lead-time boundaries, negative inputs, monotonic SS |
| TS-04 | Replenishment | MOQ round-up (4 cases), bulk approve → PO numbers & value, edit qty (MOQ multiple), reject with reason, filter, viewer |
| TS-05 | Scenarios | uplift math, baseline includes overrides, validation and boundaries, duplicate name, delete |
| API | REST | stat = final invariant, audit entry, override rules, policy math, double-approval atomicity, RBAC, scenario math |

## Getting started

```bash
git clone https://github.com/kpravinsqa/playwright-python-xpression-nextgen.git
cd playwright-python-xpression-nextgen
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
pytest                # or: pytest -m smoke | pytest -m api | pytest -n auto
```

Manual exploration: `python -m mock_app.server` → http://127.0.0.1:8000 (`planner` or `viewer`, password `Plan@123`).

## Structure

```
api/planning_client.py   pages/ (login, workbench, inventory, replenishment, scenarios)
mock_app/                tests/ui · tests/api        test_data/inventory_policy.json
```

## Author

**Pravin Khedkar**, QA Lead / SDET · [@kpravinsqa](https://github.com/kpravinsqa)
