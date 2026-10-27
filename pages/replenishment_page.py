from playwright.sync_api import Page

from pages.base_page import BasePage


class ReplenishmentPage(BasePage):
    path = "/replenishment.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.status_filter = page.get_by_test_id("status-filter")
        self.approved_value = page.get_by_test_id("approved-value")
        self.rows = page.get_by_test_id("recs-table").locator("tbody tr")
        self.approve_button = page.get_by_test_id("approve-selected")
        self.reject_panel = page.get_by_test_id("reject-panel")
        self.reject_reason = page.get_by_test_id("reject-reason")
        self.confirm_reject = page.get_by_test_id("confirm-reject")

    def open(self):
        super().open()
        self.rows.first.wait_for()
        return self

    def row(self, rid: int):
        return self.page.get_by_test_id(f"rec-{rid}")

    def status(self, rid: int):
        return self.row(rid).get_by_test_id("status")

    def qty(self, rid: int):
        return self.page.get_by_test_id(f"qty-{rid}")

    def set_qty(self, rid: int, qty: int):
        with self.page.expect_response(f"**/api/replenishment/{rid}"):
            self.qty(rid).fill(str(qty))
            self.qty(rid).press("Tab")

    def approve(self, *ids: int):
        for rid in ids:
            self.page.get_by_test_id(f"select-{rid}").check()
        self.approve_button.click()

    def reject(self, rid: int, reason: str):
        self.page.get_by_test_id(f"reject-{rid}").click()
        self.reject_reason.fill(reason)
        self.confirm_reject.click()
