import os
from app import db
from app.models import EfektUczenia, Uzytkownik

EFEKTY = [
    (1, "Wiedza z zakresu matematyki, fizyki i podstaw informatyki."),
    (2, "Umiejętność programowania w językach wysokiego poziomu."),
    (3, "Projektowanie, implementacja i administracja bazami danych."),
    (4, "Znajomość inżynierii oprogramowania i cyklu życia systemów."),
    (5, "Umiejętność pracy w zespole programistycznym i komunikacji."),
    (6, "Rozwiązywanie problemów i implementacja algorytmów."),
    (7, "Znajomość systemów operacyjnych i sieci komputerowych."),
    (8, "Metody analizy i oceny złożoności obliczeniowej algorytmów."),
    (9, "Zasady bezpieczeństwa systemów i ochrony danych osobowych."),
    (10, "Efektywne wykorzystanie środowisk i narzędzi programistycznych."),
    (11, "Rozumienie aspektów prawnych, etycznych i społecznych zawodu."),
    (12, "Zdolność do samokształcenia i ciągłego podnoszenia kwalifikacji."),
    (13, "Umiejętność tworzenia dokumentacji technicznej i projektowej.")
]

def seed_db():
    # Seed Efekty Uczenia
    for nr, opis in EFEKTY:
        existing = EfektUczenia.query.filter_by(nr=nr).first()
        if not existing:
            efekt = EfektUczenia(nr=nr, opis=opis)
            db.session.add(efekt)
            
    # Seed Test Admin User
    admin_email = "admin@ans-elblag.pl"
    existing_admin = Uzytkownik.query.filter_by(email=admin_email).first()
    if not existing_admin:
        admin = Uzytkownik(
            imie="Administrator",
            nazwisko="Systemu",
            email=admin_email,
            rola="administrator"
        )
        # Haslo admina pobierane z env (SEED_ADMIN_PASSWORD); fallback tylko dla dev.
        admin_password = os.environ.get('SEED_ADMIN_PASSWORD', 'admin123')
        admin.set_password(admin_password)
        db.session.add(admin)
        if admin_password == 'admin123':
            print("UWAGA: uzyto domyslnego hasla admina 'admin123'. Ustaw SEED_ADMIN_PASSWORD i zmien je.")
        
    db.session.commit()
    print("Database seeding completed.")
