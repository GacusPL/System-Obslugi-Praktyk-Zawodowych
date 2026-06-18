import os
from app import db
from app.models import EfektUczenia, Uzytkownik

# Opisy efektów kształcenia zgodne z oryginalnym Zał. nr 2a (ANS Elbląg, Informatyka)
EFEKTY = [
    (1, "Ma wiedzę na temat sposobu realizacji zadań inżynierskich dotyczących informatyki z zachowaniem standardów i norm technicznych"),
    (2, "Zna technologie, narzędzia, metody, techniki oraz sprzęt stosowane w informatyce"),
    (3, "Zna ekonomiczne, prawne skutki własnych działań podejmowanych w ramach praktyki oraz ograniczenia wynikające z prawa autorskiego i kodeksu pracy"),
    (4, "Zna zasady bezpieczeństwa pracy i ergonomii w zawodzie informatyka"),
    (5, "Pozyskuje informacje odnośnie technologii, metod, technik, sprzętu wymaganego do realizacji powierzonego zadania, posługując się rozmaitymi źródłami literaturowymi i zasobami publikowanymi w języku polskim jak i angielskim"),
    (6, "W oparciu o kontakty ze środowiskiem inżynierskim zakładu, potrafi podnieść swoje kompetencje, wiedzę i umiejętności, co najmniej z dwóch zakresów: zadania dotyczące sprzętu i oprogramowania: np.: programowania, administrowanie siecią komputerową, konserwacja sprzętu i oprogramowania, bieżące usuwanie usterek, administrowanie zasobami informatycznymi, zakładu pracy / instytucji, (e)usługami."),
    (7, "Opracowuje dokumentację dotyczącą realizacji podejmowanych zadań w ramach praktyki, a także referuje ustnie prezentowane w niej zagadnienia"),
    (8, "Potrafi zidentyfikować problem informatyczny występujący w zakładzie pracy / instytucji, opisać go, przedstawić koncepcję rozwiązania i ją zrealizować."),
    (9, "Potrafi rozwiązać rzeczywiste zadanie inżynierskie z zakresu działalności informatycznej zakładu pracy/instytucji stosując normy i standardy stosowane w informatyce oraz biorąc pod uwagę aspekty środowiskowe i etyczne."),
    (10, "Pracuje w zespole zajmującym się zawodowo branżą IT"),
    (11, "Przestrzega zasad etyki zawodowej i zgodnie z tymi zasadami korzysta z wiedzy i pomocy doświadczonych kolegów"),
    (12, "Kontaktując się z osobami spoza branży potrafi zarówno pozyskać od nich niezbędne informacje do realizacji planowanego zadania, jak i przekazać im w sposób zrozumiały informacje i opinie z zakresu informatyki"),
    (13, "Dostrzega w praktyce tempo deaktualizacji wiedzy informatycznej oraz skutki działalności informatyków w szczególności ekonomiczne i społeczne")
]

def seed_db():
    # Seed Efekty Uczenia (aktualizuj opis, jeśli rekord już istnieje)
    for nr, opis in EFEKTY:
        existing = EfektUczenia.query.filter_by(nr=nr).first()
        if not existing:
            efekt = EfektUczenia(nr=nr, opis=opis)
            db.session.add(efekt)
        elif existing.opis != opis:
            existing.opis = opis
            
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
