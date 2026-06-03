import pytest

def test_login_flow_and_waiting(page, server):
    # Go to login page
    page.goto(f"{server}/auth/login")
    assert "Logowanie" in page.title()
    
    # Click Admin mock login
    page.click("text=Admin")
    
    # Verify we are on the dashboard
    page.wait_for_url(f"{server}/dashboard")
    assert "Dashboard" in page.title()
    
    # Check admin role badge
    assert page.locator(".badge-admin").is_visible()
    
    # Logout
    page.click("#userMenuButton")
    page.click("text=Wyloguj")
    page.wait_for_url(f"{server}/auth/login")
