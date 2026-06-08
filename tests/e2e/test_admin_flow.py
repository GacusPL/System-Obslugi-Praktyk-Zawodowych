import pytest
import os

def test_admin_flow(page, server):
    # Login as Admin
    page.goto(f"{server}/auth/login")
    page.click("text=Admin")
    
    # Verify dashboard
    page.wait_for_url(f"{server}/dashboard")
    assert "Dashboard" in page.title()
    assert page.locator(".badge-admin").is_visible()
    
    # --- E2E-015: Eksport XLSX/CSV ---
    # 1. Download XLSX report
    with page.expect_download() as download_xlsx_info:
        page.click("text=Eksportuj protokół (XLSX)")
    xlsx_download = download_xlsx_info.value
    assert xlsx_download.suggested_filename == "oceny_usos.xlsx"
    temp_xlsx = os.path.join("D:\\Dokumenty\\GitHub\\System-Obslugi-Praktyk-Zawodowych", "oceny_usos_downloaded.xlsx")
    xlsx_download.save_as(temp_xlsx)
    assert os.path.exists(temp_xlsx)
    assert os.path.getsize(temp_xlsx) > 0
    os.remove(temp_xlsx)

    # 2. Download CSV report
    with page.expect_download() as download_csv_info:
        page.click("text=Eksportuj protokół (CSV)")
    csv_download = download_csv_info.value
    assert csv_download.suggested_filename == "oceny_usos.csv"
    temp_csv = os.path.join("D:\\Dokumenty\\GitHub\\System-Obslugi-Praktyk-Zawodowych", "oceny_usos_downloaded.csv")
    csv_download.save_as(temp_csv)
    assert os.path.exists(temp_csv)
    assert os.path.getsize(temp_csv) > 0
    os.remove(temp_csv)
    
    # Navigate to users list
    page.click("text=Lista użytkowników")
    page.wait_for_url(f"{server}/admin/users")
    assert "Zarządzanie Użytkownikami" in page.content()
    
    # Logout
    page.click("#userMenuButton")
    page.click("text=Wyloguj")
