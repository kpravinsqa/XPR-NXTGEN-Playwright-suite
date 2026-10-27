"""What-if scenarios — manual suite TS-05."""
import pytest
from playwright.sync_api import Page, expect

from pages.scenarios_page import ScenariosPage


@pytest.fixture
def sc(logged_in_page: Page) -> ScenariosPage:
    return ScenariosPage(logged_in_page).open()


@pytest.mark.ui
@pytest.mark.smoke
def test_create_uplift_scenario(sc: ScenariosPage):
    sc.create("Diwali Peak", 15)
    sc.expect_toast('Scenario "Diwali Peak" created')
    row = sc.row("Diwali Peak")
    expect(row.get_by_test_id("baseline")).to_have_text("17,150")
    expect(row.get_by_test_id("scenario-total")).to_have_text("19,722")   # round(17150 × 1.15)
    expect(row.get_by_test_id("delta")).to_have_text("+2,572")


@pytest.mark.ui
@pytest.mark.regression
def test_scenario_baseline_includes_overrides(sc: ScenariosPage, api):
    api.put("/api/demand/SKU-1001@DC-PUNE/override", data={"week": "W3", "qty": 600})
    sc.create("After Override", 0)
    expect(sc.row("After Override").get_by_test_id("baseline")).to_have_text("17,190")


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.parametrize("name, uplift, field, error", [
    ("", 10, "name", "Scenario name is required"),
    ("Too Low", -51, "uplift_pct", "Uplift must be between -50% and 100%"),
    ("Too High", 101, "uplift_pct", "Uplift must be between -50% and 100%"),
    ("Blank Uplift", None, "uplift_pct", "Uplift must be between -50% and 100%"),
], ids=["no-name", "uplift-minus-51", "uplift-101", "uplift-blank"])
def test_scenario_validation(sc: ScenariosPage, name, uplift, field, error):
    sc.create(name, uplift)
    expect(sc.field_error(field)).to_have_text(error)


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("uplift", [-50, 100], ids=["min-boundary", "max-boundary"])
def test_uplift_boundaries_accepted(sc: ScenariosPage, uplift):
    sc.create(f"Edge {uplift}", uplift)
    sc.expect_toast("created")


@pytest.mark.ui
@pytest.mark.regression
def test_duplicate_name_and_delete(sc: ScenariosPage):
    sc.create("Monsoon", -10)
    sc.expect_toast('Scenario "Monsoon" created')
    sc.create("monsoon", 5)
    expect(sc.field_error("name")).to_have_text("Scenario name already exists")
    sc.delete("Monsoon")
    expect(sc.empty_state).to_be_visible()
