import pytest
import time

def test_complete_student_to_uopz_e2e_flow(page, server):
    # --- 1. STUDENT REGISTERS PRACTICE ---
    page.goto(f"{server}/auth/login")
    page.click("text=Student (Jan Kowalski)")
    page.wait_for_url(f"{server}/dashboard")
    
    # Navigate to zgloszenie
    page.click("a[href='/praktyka/zgloszenie']")
    page.wait_for_url(f"{server}/praktyka/zgloszenie")
    
    # Fill standard practice form
    page.select_option("select[name='zaklad_id']", index=1)
    page.select_option("select[name='uopz_id']", index=1)
    page.fill("input[name='rok_akademicki']", "2025/2026")
    page.fill("input[name='termin_od']", "2026-07-01")
    page.fill("input[name='termin_do']", "2026-09-30")
    page.click("button[type='submit']")
    
    # Verify redirected back to dashboard
    page.wait_for_url(f"{server}/dashboard")
    assert "Aktywna Praktyka" in page.content() or "Firma Testowa" in page.content()
    
    # Logout Student
    page.click("#userMenuButton")
    page.click("text=Wyloguj")
    page.wait_for_url(f"{server}/auth/login")

    # --- 2. UOPZ CHECKS DASHBOARD ---
    page.click("text=UOPZ")
    page.wait_for_url(f"{server}/dashboard")
    assert "Anna Nowak" in page.content() or "uopz" in page.content()
    assert "Firma Testowa" in page.content()
    
    # Logout UOPZ
    page.click("#userMenuButton")
    page.click("text=Wyloguj")
    page.wait_for_url(f"{server}/auth/login")
