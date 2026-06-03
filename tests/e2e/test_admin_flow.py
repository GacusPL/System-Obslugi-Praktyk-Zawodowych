import pytest

def test_admin_flow(page, server):
    # Login as Admin
    page.goto(f"{server}/auth/login")
    page.click("text=Admin")
    
    # Verify dashboard
    page.wait_for_url(f"{server}/dashboard")
    assert "Dashboard" in page.title()
    assert page.locator(".badge-admin").is_visible()
    
    # Navigate to users list
    page.click("text=Lista użytkowników")
    page.wait_for_url(f"{server}/admin/users")
    assert "Zarządzanie Użytkownikami" in page.content()
    
    # Logout
    page.click("#userMenuButton")
    page.click("text=Wyloguj")
