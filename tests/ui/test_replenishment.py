"""Replenishment recommendations — manual suite TS-04."""
import pytest
from playwright.sync_api import Page, expect

from config.settings import settings
from pages.login_page import LoginPage
from pages.replenishment_page import ReplenishmentPage


@pytest.fixture
def rp(logged_in_page: Page) -> ReplenishmentPage:
    return ReplenishmentPage(logged_in_page).open()


@pytest.mark.ui
@pytest.mark.smoke
@pytest.mark.parametrize("rid, required, recommended", [(500, 1130, 1250), (501, 430, 500), (502, 95, 96), (503, 2500, 2500)],
                         ids=["round-up-250", "round-up-100", "round-up-48", "exact-multiple"])
def test_recommended_qty_rounded_up_to_moq(rp: ReplenishmentPage, rid, required, recommended):
    expect(rp.row(rid).get_by_test_id("required")).to_have_text(str(required))
    expect(rp.qty(rid)).to_have_value(str(recommended))


@pytest.mark.ui
@pytest.mark.smoke
def test_bulk_approve_generates_po_numbers(rp: ReplenishmentPage):
    rp.approve(500, 502)
    rp.expect_toast("2 recommendation(s) approved")
    expect(rp.status(500)).to_have_text("APPROVED")
    expect(rp.row(500).get_by_test_id("po")).to_have_text("PO-000500")
    expect(rp.status(501)).to_have_text("PROPOSED")
    expect(rp.approved_value).to_have_text("$2960.50")      # 2312.50 + 648.00


@pytest.mark.ui
@pytest.mark.regression
def test_approve_button_requires_selection(rp: ReplenishmentPage):
    expect(rp.approve_button).to_be_disabled()


@pytest.mark.ui
@pytest.mark.regression
def test_edit_qty_to_moq_multiple_recalculates_value(rp: ReplenishmentPage):
    rp.set_qty(501, 700)
    rp.expect_toast("Quantity updated")
    expect(rp.row(501).get_by_test_id("value")).to_have_text("$2940.00")


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
def test_edit_qty_not_multiple_of_moq_rejected(rp: ReplenishmentPage):
    rp.set_qty(501, 650)
    rp.expect_toast("Quantity must be a multiple of the MOQ (100)")
    expect(rp.qty(501)).to_have_value("500")


@pytest.mark.ui
@pytest.mark.regression
def test_reject_requires_reason(rp: ReplenishmentPage):
    rp.reject(503, "no")
    expect(rp.field_error("reason")).to_have_text("Please give a rejection reason (min 5 characters)")
    rp.reject_reason.fill("Supplier on credit hold")
    rp.confirm_reject.click()
    rp.expect_toast("Recommendation #503 rejected")
    expect(rp.status(503)).to_have_text("REJECTED")


@pytest.mark.ui
@pytest.mark.regression
def test_status_filter(rp: ReplenishmentPage, api):
    api.post("/api/replenishment/approve", data={"ids": [500]})
    rp.page.reload()
    rp.status_filter.select_option("APPROVED")
    expect(rp.rows).to_have_count(1)


@pytest.mark.ui
@pytest.mark.regression
def test_viewer_sees_read_only_recommendations(page: Page):
    login = LoginPage(page).open()
    login.login(*settings.viewer)
    rp = ReplenishmentPage(page).open()
    expect(rp.qty(500)).to_be_disabled()
    expect(page.get_by_test_id("select-500")).to_have_count(0)
