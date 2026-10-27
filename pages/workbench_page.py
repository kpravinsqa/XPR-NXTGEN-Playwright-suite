from playwright.sync_api import Page

from pages.base_page import BasePage


class WorkbenchPage(BasePage):
    path = "/workbench.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.location_filter = page.get_by_test_id("location-filter")
        self.reason_code = page.get_by_test_id("reason-code")
        self.grand_total = page.get_by_test_id("grand-total")
        self.final_rows = page.locator("[data-testid^='final-']")

    def open(self):
        super().open()
        self.grand_total.filter(has_text="1").wait_for()
        return self

    def cell(self, key: str, week: str):
        return self.page.get_by_test_id(f"cell-{key}-{week}")

    def total_final(self, key: str):
        return self.page.get_by_test_id(f"final-{key}").get_by_test_id("total-final")

    def override(self, key: str, week: str, qty, reason: str | None = None):
        self.reason_code.select_option(reason or "")
        cell = self.cell(key, week)
        with self.page.expect_response("**/override"):
            cell.fill("" if qty is None else str(qty))
            cell.press("Tab")
