import pytest

def test_full_student_flow(page, server):
    # 1. Login as student
    page.goto(f"{server}/auth/login")
    assert "Logowanie" in page.title()
    page.click("text=Student (Jan Kowalski)")
    
    # Verify dashboard
    page.wait_for_url(f"{server}/dashboard")
    assert "Dashboard" in page.title()
    assert page.locator(".badge-student").is_visible()

    # 2. Register practice (P1) - skip if already registered by another test
    if page.locator("a[href='/praktyka/zgloszenie']").is_visible():
        page.click("a[href='/praktyka/zgloszenie']")
        page.wait_for_url(f"{server}/praktyka/zgloszenie")
        
        # Fill out the form
        page.select_option("select[name='zaklad_id']", index=1)
        page.select_option("select[name='uopz_id']", index=1)
        page.fill("input[name='rok_akademicki']", "2025/2026")
        page.fill("input[name='termin_od']", "2026-07-01")
        page.fill("input[name='termin_do']", "2026-09-30")
        page.click("button[type='submit']")
        
        # Verify redirected back to dashboard
        page.wait_for_url(f"{server}/dashboard")
    
    # Logout
    page.click("#userMenuButton")
    page.click("text=Wyloguj")
    page.wait_for_url(f"{server}/auth/login")
