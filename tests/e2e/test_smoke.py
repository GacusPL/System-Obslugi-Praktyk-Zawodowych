import pytest

def test_smoke_login_page(page, server):
    # Open base url (should redirect to auth/login)
    page.goto(server)
    page.wait_for_url(f"{server}/auth/login")
    
    assert "Logowanie" in page.title()
    
    # Check if Bootstrap CSS and custom CSS are loaded
    assert page.evaluate("() => document.styleSheets.length") > 0
    
    # Check that main container is visible
    assert page.locator(".login-card").is_visible()
    
    # Check if Microsoft login button exists
    btn = page.locator("a:has-text('Zaloguj przez konto Microsoft')")
    assert btn.is_visible()
