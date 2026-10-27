from playwright.sync_api import Page

from pages.base_page import BasePage


class InventoryPolicyPage(BasePage):
    path = "/inventory.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.avg = page.get_by_test_id("avg_daily_demand")
        self.std = page.get_by_test_id("demand_std_dev")
        self.lead_time = page.get_by_test_id("lead_time_days")
        self.service_level = page.get_by_test_id("service_level")
        self.calculate_button = page.get_by_test_id("calculate")
        self.results = page.get_by_test_id("results")
        self.z = page.get_by_test_id("z")
        self.safety_stock = page.get_by_test_id("safety-stock")
        self.reorder_point = page.get_by_test_id("reorder-point")

    def calculate(self, avg, std, lead_time, service_level=95):
        self.avg.fill(str(avg))
        self.std.fill(str(std))
        self.lead_time.fill(str(lead_time))
        self.service_level.select_option(str(service_level))
        self.calculate_button.click()
