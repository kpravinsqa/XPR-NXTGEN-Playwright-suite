from playwright.sync_api import Page

from pages.base_page import BasePage


class ScenariosPage(BasePage):
    path = "/scenarios.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.name = page.get_by_test_id("scenario-name")
        self.uplift = page.get_by_test_id("uplift")
        self.create_button = page.get_by_test_id("create-scenario")
        self.rows = page.get_by_test_id("scenarios-table").locator("tbody tr")
        self.empty_state = page.get_by_test_id("no-scenarios")

    def create(self, name: str, uplift):
        self.name.fill(name)
        self.uplift.fill("" if uplift is None else str(uplift))
        self.create_button.click()

    def row(self, name: str):
        return self.page.get_by_test_id(f"scenario-{name}")

    def delete(self, name: str):
        self.page.get_by_test_id(f"delete-{name}").click()
