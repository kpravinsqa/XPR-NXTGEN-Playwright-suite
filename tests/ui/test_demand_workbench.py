"""Demand workbench overrides — manual suite TS-02."""
import pytest
from playwright.sync_api import Page, expect

from config.settings import settings
from pages.login_page import LoginPage
from pages.workbench_page import WorkbenchPage

OAT = "SKU-1001@DC-PUNE"          # stat W3 = 560, total 4 570
BOTTLE = "SKU-2001@DC-MUMBAI"     # stat W5 = 100


@pytest.fixture
def wb(logged_in_page: Page) -> WorkbenchPage:
    return WorkbenchPage(logged_in_page).open()


@pytest.mark.ui
@pytest.mark.smoke
def test_grid_loads_with_statistical_totals(wb: WorkbenchPage):
    expect(wb.final_rows).to_have_count(4)
    expect(wb.grand_total).to_have_text("17,150")
    expect(wb.total_final(OAT)).to_have_text("4570")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("week", ["W1", "W2"])
def test_frozen_horizon_cells_are_locked(wb: WorkbenchPage, week):
    expect(wb.cell(OAT, week)).to_be_disabled()


@pytest.mark.ui
@pytest.mark.smoke
def test_override_within_threshold_updates_totals(wb: WorkbenchPage):
    wb.override(OAT, "W3", 600)                  # +7.1 %, no reason needed
    wb.expect_toast("Override saved for SKU-1001 W3")
    expect(wb.total_final(OAT)).to_have_text("4610")
    expect(wb.grand_total).to_have_text("17,190")
    expect(wb.cell(OAT, "W3")).to_have_class("cell overridden")


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.parametrize("qty", [121, 79], ids=["+21pct", "-21pct"])
def test_override_above_threshold_requires_reason(wb: WorkbenchPage, qty):
    wb.override(BOTTLE, "W5", qty)
    wb.expect_toast("A reason code is required for changes above 20%")
    expect(wb.cell(BOTTLE, "W5")).to_have_value("100")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.parametrize("qty", [120, 80], ids=["+20pct-boundary", "-20pct-boundary"])
def test_override_at_exact_threshold_needs_no_reason(wb: WorkbenchPage, qty):
    wb.override(BOTTLE, "W5", qty)
    wb.expect_toast("Override saved")


@pytest.mark.ui
@pytest.mark.regression
def test_large_override_with_reason_code(wb: WorkbenchPage):
    wb.override(BOTTLE, "W5", 250, reason="PROMOTION")
    wb.expect_toast("Override saved for SKU-2001 W5")
    expect(wb.cell(BOTTLE, "W5")).to_have_value("250")


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.parametrize("value", ["-5", "12.5", "1000001"], ids=["negative", "decimal", "above-max"])
def test_invalid_override_values(wb: WorkbenchPage, value):
    wb.override(OAT, "W4", value, reason="SEASONALITY")
    wb.expect_toast("Override must be a whole number between 0 and 1,000,000")


@pytest.mark.ui
@pytest.mark.regression
def test_clear_override_reverts_to_statistical(wb: WorkbenchPage):
    wb.override(OAT, "W3", 600)
    expect(wb.total_final(OAT)).to_have_text("4610")
    wb.override(OAT, "W3", None)
    wb.expect_toast("Override cleared for SKU-1001 W3")
    expect(wb.cell(OAT, "W3")).to_have_value("560")
    expect(wb.total_final(OAT)).to_have_text("4570")


@pytest.mark.ui
@pytest.mark.regression
def test_location_filter(wb: WorkbenchPage):
    wb.location_filter.select_option("DC-MUMBAI")
    expect(wb.final_rows).to_have_count(2)
    expect(wb.grand_total).to_have_text("10,800")


@pytest.mark.ui
@pytest.mark.regression
def test_viewer_cannot_edit_grid(page: Page):
    login = LoginPage(page).open()
    login.login(*settings.viewer)
    wb = WorkbenchPage(page)
    expect(wb.cell(OAT, "W5")).to_be_disabled()
