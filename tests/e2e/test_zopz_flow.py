import pytest

def test_zopz_verification_flow(page, server):
    # Login as ZOPZ
    page.goto(f"{server}/auth/login")
    page.click("text=ZOPZ")
    
    # Verify dashboard
    page.wait_for_url(f"{server}/dashboard")
    assert "Dashboard" in page.title()
    assert page.locator(".badge-zopz").is_visible()
    
    # Logout
    page.click("#userMenuButton")
    page.click("text=Wyloguj")
