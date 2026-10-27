"""Safety stock & reorder point — manual suite TS-03."""
import pytest
from playwright.sync_api import Page, expect

from pages.inventory_page import InventoryPolicyPage
from utils.data_loader import cases


@pytest.fixture
def policy(logged_in_page: Page) -> InventoryPolicyPage:
    return InventoryPolicyPage(logged_in_page).open()


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("case", cases("inventory_policy", "policy_cases"))
def test_safety_stock_and_reorder_point(policy: InventoryPolicyPage, case):
    policy.calculate(case["avg"], case["std"], case["lead_time"], case["service_level"])
    expect(policy.z).to_have_text(str(case["z"]))
    expect(policy.safety_stock).to_have_text(str(case["safety_stock"]))
    expect(policy.reorder_point).to_have_text(str(case["reorder_point"]))


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.parametrize("case", cases("inventory_policy", "invalid_inputs"))
def test_policy_input_validation(policy: InventoryPolicyPage, case):
    policy.calculate(case["avg"], case["std"], case["lead_time"])
    expect(policy.field_error(case["field"])).to_have_text(case["error"])
    expect(policy.results).to_be_hidden()


@pytest.mark.ui
@pytest.mark.smoke
def test_higher_service_level_never_lowers_safety_stock(policy: InventoryPolicyPage):
    previous = -1
    for sl in (90, 95, 98, 99):
        policy.calculate(250, 45, 12, sl)
        expect(policy.results).to_be_visible()
        expect(policy.z).not_to_have_text("")
        current = int(policy.safety_stock.inner_text())
        assert current >= previous
        previous = current
