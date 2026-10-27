from playwright.sync_api import APIRequestContext


class PlanningClient:
    def __init__(self, ctx: APIRequestContext):
        self.ctx = ctx

    def demand(self, location=None):
        return self.ctx.get("/api/demand", params={"location": location} if location else None)

    def override(self, key, week, qty, reason=None):
        return self.ctx.put(f"/api/demand/{key}/override", data={"week": week, "qty": qty, "reason": reason})

    def policy(self, **inputs):
        return self.ctx.post("/api/inventory/policy", data=inputs)

    def recs(self, status=None):
        return self.ctx.get("/api/replenishment", params={"status": status} if status else None)

    def edit_rec(self, rid, qty):
        return self.ctx.put(f"/api/replenishment/{rid}", data={"qty": qty})

    def approve(self, ids):
        return self.ctx.post("/api/replenishment/approve", data={"ids": ids})

    def reject(self, rid, reason):
        return self.ctx.post(f"/api/replenishment/{rid}/reject", data={"reason": reason})

    def create_scenario(self, name, uplift_pct):
        return self.ctx.post("/api/scenarios", data={"name": name, "uplift_pct": uplift_pct})
