import pytest

def test_responsive_mobile_layout(page, server):
    # Set mobile viewport
    page.set_viewport_size({"width": 375, "height": 667})
    
    # Go to login page
    page.goto(f"{server}/auth/login")
    assert "Logowanie" in page.title()
    
    # Log in as Student
    page.click("text=Student (Jan Kowalski)")
    page.wait_for_url(f"{server}/dashboard")
    
    # Check if toggle is visible
    toggle = page.locator(".navbar-toggler")
    assert toggle.is_visible()
    
    # Click toggle and verify nav links are visible
    toggle.click()
    page.wait_for_selector(".navbar-collapse.show")
    
    # Logout
    page.click("#userMenuButton")
    page.click("text=Wyloguj")
