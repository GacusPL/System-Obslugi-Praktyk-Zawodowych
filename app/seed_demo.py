import os
from datetime import date, datetime, timedelta
from app import db
from app.models import (
    EfektUczenia, Uzytkownik, Student, ZakladPracy, Praktyka,
    Harmonogram, HarmonogramDzial, WpisDziennika, PotwierdzenieEfektow,
    PotwierdzenieEfektOcena, Sprawozdanie, KartaPraktyki, Ankieta,
    AnkietaOdpowiedz, WniosekAlternatywny, ZalacznikSkan, Egzamin,
    KomisjaCzlonek
)

def seed_demo_db():
    print("Starting demo database seeding...")

    # 1. Ensure learning outcomes (Efekty) are seeded first
    from app.seed import seed_db
    seed_db()

    # 2. Add Demo Users
    users_data = [
        ("uopz@ans-elblag.pl", "Anna", "Nowak", "uopz", "uopz123"),
        ("zopz@ans-elblag.pl", "Adam", "Zopz", "zopz", "zopz123"),
        ("zopz2@ans-elblag.pl", "Marek", "Kowalski", "zopz", "zopz123"),
        ("dyrektor@ans-elblag.pl", "Jan", "Dyrektor", "dyrektor", "dyrektor123"),
        ("student1@ans-elblag.pl", "Kacper", "Student", "student", "student123"),
        ("student2@ans-elblag.pl", "Jan", "Kowalski", "student", "student123"),
        ("student3@ans-elblag.pl", "Michał", "Wiśniewski", "student", "student123")
    ]

    users = {}
    for email, imie, nazwisko, rola, password in users_data:
        user = Uzytkownik.query.filter_by(email=email).first()
        if not user:
            user = Uzytkownik(imie=imie, nazwisko=nazwisko, email=email, rola=rola)
            user.set_password(password)
            db.session.add(user)
        else:
            user.imie = imie
            user.nazwisko = nazwisko
            user.rola = rola
            user.set_password(password)
        db.session.commit()
        users[email] = user

    # 3. Add Demo Students
    student1_profile = Student.query.filter_by(nr_albumu="22334").first()
    if not student1_profile:
        student1_profile = Student(
            uzytkownik_id=users["student1@ans-elblag.pl"].id,
            nr_albumu="22334",
            kierunek="Informatyka",
            specjalnosc="Inżynieria Oprogramowania",
            semestr=6,
            forma_studiow="stacjonarne",
            rok_akademicki="2025/2026"
        )
        db.session.add(student1_profile)

    student2_profile = Student.query.filter_by(nr_albumu="12345").first()
    if not student2_profile:
        student2_profile = Student(
            uzytkownik_id=users["student2@ans-elblag.pl"].id,
            nr_albumu="12345",
            kierunek="Informatyka",
            specjalnosc="Inżynieria Oprogramowania",
            semestr=7,
            forma_studiow="stacjonarne",
            rok_akademicki="2025/2026"
        )
        db.session.add(student2_profile)

    student3_profile = Student.query.filter_by(nr_albumu="54321").first()
    if not student3_profile:
        student3_profile = Student(
            uzytkownik_id=users["student3@ans-elblag.pl"].id,
            nr_albumu="54321",
            kierunek="Informatyka",
            specjalnosc="Inżynieria Systemów",
            semestr=6,
            forma_studiow="stacjonarne",
            rok_akademicki="2025/2026"
        )
        db.session.add(student3_profile)
    db.session.commit()

    # 4. Add Demo Workplaces (Zakłady Pracy)
    zp1 = ZakladPracy.query.filter_by(nip="1234567890").first()
    if not zp1:
        zp1 = ZakladPracy(
            nazwa="SoftDev Sp. z o.o.",
            adres="Elbląg, ul. Grunwaldzka 12",
            nip="1234567890",
            zopz_imie="Adam",
            zopz_nazwisko="Zopz",
            zopz_stanowisko="Senior Tech Lead",
            zopz_wyksztalcenie="Wyższe magisterskie",
            status="Approved"
        )
        db.session.add(zp1)

    zp2 = ZakladPracy.query.filter_by(nip="9876543210").first()
    if not zp2:
        zp2 = ZakladPracy(
            nazwa="Global IT Solutions",
            adres="Elbląg, ul. 1 Maja 45",
            nip="9876543210",
            zopz_imie="Marek",
            zopz_nazwisko="Kowalski",
            zopz_stanowisko="Dyrektor HR",
            zopz_wyksztalcenie="Wyższe",
            status="Approved"
        )
        db.session.add(zp2)
    db.session.commit()

    # 5. Student 1: Active Draft Practice (Draft)
    praktyka1 = Praktyka.query.filter_by(student_id=student1_profile.id).first()
    if not praktyka1:
        praktyka1 = Praktyka(
            student_id=student1_profile.id,
            zaklad_id=zp1.id,
            uopz_id=users["uopz@ans-elblag.pl"].id,
            termin_od=date(2026, 7, 1),
            termin_do=date(2026, 9, 30),
            rok_akademicki="2025/2026",
            status="Draft"
        )
        db.session.add(praktyka1)
        db.session.commit()

    # 6. Student 2: Fully Completed & Closed Practice (Closed)
    praktyka2 = Praktyka.query.filter_by(student_id=student2_profile.id).first()
    if not praktyka2:
        praktyka2 = Praktyka(
            student_id=student2_profile.id,
            zaklad_id=zp1.id,
            uopz_id=users["uopz@ans-elblag.pl"].id,
            termin_od=date(2025, 7, 1),
            termin_do=date(2025, 9, 30),
            rok_akademicki="2025/2026",
            status="Closed",
            ocena_koncowa=5.0,
            ankieta_wypelniona=1,
            dziennik_status="Closed"
        )
        db.session.add(praktyka2)
        db.session.commit()

        # Seed Harmonogram for completed practice
        h = Harmonogram(
            praktyka_id=praktyka2.id,
            podpis_student=1,
            podpis_zopz=1,
            podpis_uopz=1,
            status="Approved"
        )
        db.session.add(h)
        db.session.commit()

        # Działy harmonogramu
        dz1 = HarmonogramDzial(harmonogram_id=h.id, nazwa_dzialu="Projektowanie i przygotowanie środowiska", planowane_dni=30)
        dz2 = HarmonogramDzial(harmonogram_id=h.id, nazwa_dzialu="Implementacja backendu i API", planowane_dni=50)
        dz3 = HarmonogramDzial(harmonogram_id=h.id, nazwa_dzialu="Wdrożenie i testy automatyczne", planowane_dni=40)
        db.session.add_all([dz1, dz2, dz3])
        db.session.commit()

        # Dziennik: 120 dni wpisów
        start_date = date(2025, 7, 1)
        efekty = EfektUczenia.query.all()
        for d in range(1, 121):
            wpis_date = start_date + timedelta(days=d-1)
            wpis = WpisDziennika(
                praktyka_id=praktyka2.id,
                dzien_nr=d,
                data_wpisu=wpis_date,
                opis_prac=f"Prace projektowo-programistyczne w systemie SOPZ, realizacja zadań sprintu - dzień {d}.",
                status="Approved",
                podpis_zopz=1
            )
            # Link to some learning outcomes
            wpis.efekty.append(efekty[d % 13])
            wpis.efekty.append(efekty[(d + 3) % 13])
            db.session.add(wpis)
        db.session.commit()

        # Potwierdzenie efektów
        pe = PotwierdzenieEfektow(
            praktyka_id=praktyka2.id,
            godziny_zrealizowane=960,
            opinia_uopz="Student wykazał się znakomitą znajomością algorytmów oraz inżynierii oprogramowania. Zdecydowanie polecam.",
            status="Approved"
        )
        db.session.add(pe)
        db.session.commit()

        # Ocena wszystkich 13 efektów
        for e in efekty:
            peo = PotwierdzenieEfektOcena(potwierdzenie_id=pe.id, efekt_id=e.id, uzyskano=1)
            db.session.add(peo)
        db.session.commit()

        # Sprawozdanie
        spr = Sprawozdanie(
            praktyka_id=praktyka2.id,
            sekcja_I="Opis zadań zrealizowanych podczas praktyk: Prace programistyczne w języku Python i Flask, projektowanie bazy danych oraz automatyzacja testów.",
            sekcja_II="Weryfikacja uzyskanych efektów uczenia się: Nauczyłem się programowania asynchronicznego, wdrożeń Dockerowych oraz konfiguracji serwerów Nginx.",
            sekcja_III="Uwagi i wnioski końcowe: Praktyka przebiegła wzorowo. Warunki pracy były świetne, a opiekun służył fachową wiedzą techniczną.",
            wersja=1,
            ocena=5.0,
            status="Approved"
        )
        db.session.add(spr)
        db.session.commit()

        # Karta Praktyki
        kp = KartaPraktyki(
            praktyka_id=praktyka2.id,
            ocena_param_zopz=5.0,
            ocena_opisowa_zopz="Wzorowy student, samodzielny, chętny do nauki nowych technologii.",
            ocena_param_uopz=5.0,
            ocena_opisowa_uopz="Praktyka zaliczona na ocenę celującą.",
            ocena_sprawozdania=5.0,
            status="Closed"
        )
        db.session.add(kp)
        db.session.commit()

        # Egzamin
        eg = Egzamin(
            praktyka_id=praktyka2.id,
            termin=datetime(2025, 10, 15, 10, 0),
            ocena_ustna=5.0,
            ocena_koncowa=5.0,
            status="Approved"
        )
        db.session.add(eg)
        db.session.commit()

        kc1 = KomisjaCzlonek(egzamin_id=eg.id, uzytkownik_id=users["uopz@ans-elblag.pl"].id, rola_w_komisji="przewodniczacy")
        kc2 = KomisjaCzlonek(egzamin_id=eg.id, uzytkownik_id=users["dyrektor@ans-elblag.pl"].id, rola_w_komisji="czlonek")
        db.session.add_all([kc1, kc2])
        db.session.commit()

        # Ankieta
        ank = Ankieta(
            rok_akademicki="2025/2026",
            kierunek="Informatyka",
            forma_studiow="stacjonarne",
            semestr=7,
            godziny=960,
            uwagi="Bardzo dobre praktyki, dużo się nauczyłem."
        )
        db.session.add(ank)
        db.session.commit()

        for q in range(1, 15):
            ao = AnkietaOdpowiedz(ankieta_id=ank.id, pytanie_nr=q, odpowiedz=5)
            db.session.add(ao)
        db.session.commit()

    # 7. Student 1: Alternative Path Application (Wniosek Alternatywny)
    wniosek = WniosekAlternatywny.query.filter_by(student_id=student1_profile.id).first()
    if not wniosek:
        wniosek = WniosekAlternatywny(
            student_id=student1_profile.id,
            typ="praca_zawodowa",
            uzasadnienie="Pracuję jako Młodszy Programista w firmie Global IT Solutions na pełen etat od ponad roku. Zakres moich obowiązków pokrywa się z efektami uczenia się dla praktyki zawodowej.",
            status="Submitted"
        )
        db.session.add(wniosek)
        db.session.commit()

        skan = ZalacznikSkan(
            wniosek_id=wniosek.id,
            nazwa_pliku="umowa_o_prace.pdf",
            sciezka_pliku="uploads/alternative/umowa_o_prace.pdf",
            typ_dokumentu="umowa_o_prace"
        )
        db.session.add(skan)
        db.session.commit()

    # 8. Student 3: Active Under_Review Practice at zp2 (Global IT Solutions)
    praktyka3 = Praktyka.query.filter_by(student_id=student3_profile.id).first()
    if not praktyka3:
        praktyka3 = Praktyka(
            student_id=student3_profile.id,
            zaklad_id=zp2.id,
            uopz_id=users["uopz@ans-elblag.pl"].id,
            termin_od=date(2026, 7, 1),
            termin_do=date(2026, 9, 30),
            rok_akademicki="2025/2026",
            status="Under_Review"
        )
        db.session.add(praktyka3)
        db.session.commit()

        # Add 5 submitted journal logs for ZOPZ (Marek Kowalski) to sign
        start_date = date(2026, 7, 1)
        efekty = EfektUczenia.query.all()
        for d in range(1, 6):
            wpis_date = start_date + timedelta(days=d-1)
            wpis = WpisDziennika(
                praktyka_id=praktyka3.id,
                dzien_nr=d,
                data_wpisu=wpis_date,
                opis_prac=f"Wprowadzenie do systemów IT w firmie Global IT Solutions - dzień {d}.",
                status="Submitted"
            )
            if efekty:
                wpis.efekty.append(efekty[d % len(efekty)])
            db.session.add(wpis)
        db.session.commit()

    print("Demo database seeding completed successfully.")
