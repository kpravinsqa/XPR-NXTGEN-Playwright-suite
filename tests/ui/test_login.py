"""Login — manual suite TS-01."""
import re

import pytest
from playwright.sync_api import Page, expect

from config.settings import settings
from pages.login_page import LoginPage


@pytest.mark.ui
@pytest.mark.smoke
def test_planner_login(page: Page):
    login = LoginPage(page).open()
    login.login(settings.username, settings.password)
    login.wait_for_post_login()
    expect(login.user_badge).to_have_text("Demand Planner")


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
@pytest.mark.parametrize("user, pwd", [("planner", "x"), ("ghost", "Plan@123"), (" planner ", "Plan@123 ")],
                         ids=["bad-password", "unknown-user", "password-trailing-space"])
def test_invalid_login(page: Page, user, pwd):
    login = LoginPage(page).open()
    login.login(user, pwd)
    login.expect_form_error("Invalid username or password")


@pytest.mark.ui
@pytest.mark.negative
@pytest.mark.regression
def test_required_fields(page: Page):
    login = LoginPage(page).open()
    login.submit.click()
    expect(login.field_error("username")).to_have_text("Username is required")
    expect(login.field_error("password")).to_have_text("Password is required")


@pytest.mark.ui
@pytest.mark.regression
def test_unauthenticated_deep_link_redirects_to_login(page: Page):
    page.goto("/replenishment.html")
    expect(page).to_have_url(re.compile(r".*/login\.html$"))
