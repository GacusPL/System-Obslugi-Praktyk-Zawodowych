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

def test_oauth_full_flow_and_role_assignment(page, server):
    # 1. New user logs in (without role)
    page.goto(f"{server}/auth/login?mock_email=nowy.user@ans-elblag.pl")
    
    # User should be redirected to waiting page because role is None
    page.wait_for_url(f"{server}/auth/waiting")
    assert "oczekuje" in page.content()

    # Logout
    page.click("text=Wyloguj")
    page.wait_for_url(f"{server}/auth/login")

    # 2. Admin logs in to assign role
    page.goto(f"{server}/auth/login?mock_email=admin@ans-elblag.pl&mock_rola=admin")
    page.wait_for_url(f"{server}/dashboard")
    
    # Go to user management page
    page.click("text=Lista użytkowników")
    page.wait_for_url(f"{server}/admin/users")
    
    # Find the row for nowy.user@ans-elblag.pl and change role
    row = page.locator("tr", has_text="nowy.user@ans-elblag.pl")
    row.locator("select[name='rola']").select_option("student")
    row.locator("button:has-text('Zapisz')").click()
    
    # Logout Admin
    page.click("#userMenuButton")
    page.click("text=Wyloguj")
    page.wait_for_url(f"{server}/auth/login")

    # 3. New user logs in again
    page.goto(f"{server}/auth/login?mock_email=nowy.user@ans-elblag.pl")
    
    # Now they should be redirected to Student Dashboard instead of waiting page!
    page.wait_for_url(f"{server}/dashboard")
    assert "Dashboard" in page.title()
    
    # Logout
    page.click("#userMenuButton")
    page.click("text=Wyloguj")
    page.wait_for_url(f"{server}/auth/login")
