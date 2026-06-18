from datetime import date, datetime, timedelta
from app import db
from app.models import (
    EfektUczenia, Uzytkownik, Student, ZakladPracy, Praktyka,
    Harmonogram, HarmonogramDzial, ProgramPraktykiPozycja, WpisDziennika,
    PotwierdzenieEfektow, PotwierdzenieEfektOcena, Sprawozdanie, KartaPraktyki,
    Ankieta, AnkietaOdpowiedz, WniosekAlternatywny, ZalacznikSkan, Egzamin,
    KomisjaCzlonek
)


def _user(email, imie, nazwisko, rola, password):
    user = Uzytkownik.query.filter_by(email=email).first()
    if not user:
        user = Uzytkownik(imie=imie, nazwisko=nazwisko, email=email, rola=rola)
        db.session.add(user)
    else:
        user.imie, user.nazwisko, user.rola = imie, nazwisko, rola
    user.set_password(password)
    db.session.commit()
    return user


def _student(user, album, kierunek, specjalnosc, semestr, forma, rok):
    s = Student.query.filter_by(nr_albumu=album).first()
    if not s:
        s = Student(uzytkownik_id=user.id, nr_albumu=album, kierunek=kierunek,
                    specjalnosc=specjalnosc, semestr=semestr, forma_studiow=forma,
                    rok_akademicki=rok)
        db.session.add(s)
        db.session.commit()
    return s


def _harmonogram(praktyka, efekty, signatures=(1, 1, 1), status='Approved'):
    h = Harmonogram(praktyka_id=praktyka.id, podpis_student=signatures[0],
                    podpis_zopz=signatures[1], podpis_uopz=signatures[2], status=status)
    db.session.add(h)
    db.session.commit()
    for nazwa, dni in [("Projektowanie i przygotowanie środowiska", 30),
                       ("Implementacja backendu i API", 50),
                       ("Wdrożenie i testy automatyczne", 40)]:
        db.session.add(HarmonogramDzial(harmonogram_id=h.id, nazwa_dzialu=nazwa, planowane_dni=dni))
    for e in efekty:
        db.session.add(ProgramPraktykiPozycja(
            harmonogram_id=h.id, efekt_id=e.id,
            opis_realizacji=f"Realizacja efektu nr {e.nr} poprzez powierzone zadania programistyczne."))
    db.session.commit()
    return h


def _wpisy(praktyka, efekty, start_date, n_approved, n_submitted=0):
    for d in range(1, n_approved + n_submitted + 1):
        status = 'Approved' if d <= n_approved else 'Submitted'
        w = WpisDziennika(
            praktyka_id=praktyka.id, dzien_nr=d, data_wpisu=start_date + timedelta(days=d - 1),
            opis_prac=f"Realizacja zadań sprintu - dzień {d}: implementacja, testy oraz dokumentacja techniczna.",
            status=status, podpis_zopz=1 if status == 'Approved' else 0)
        if efekty:
            w.efekty.append(efekty[d % len(efekty)])
            w.efekty.append(efekty[(d + 3) % len(efekty)])
        db.session.add(w)
    db.session.commit()


def _efekty_potw(praktyka, efekty, status='Approved'):
    pe = PotwierdzenieEfektow(praktyka_id=praktyka.id, godziny_zrealizowane=960,
                              opinia_uopz="Student zrealizował wszystkie zakładane efekty uczenia się.",
                              status=status)
    db.session.add(pe)
    db.session.commit()
    for e in efekty:
        db.session.add(PotwierdzenieEfektOcena(potwierdzenie_id=pe.id, efekt_id=e.id, uzyskano=1))
    db.session.commit()
    return pe


def _sprawozdanie(praktyka, status='Approved'):
    spr = Sprawozdanie(
        praktyka_id=praktyka.id,
        sekcja_I="Opis zadań zrealizowanych podczas praktyki: prace programistyczne w języku Python i Flask, projektowanie schematu bazy danych oraz automatyzacja testów jednostkowych i integracyjnych.",
        sekcja_II="Weryfikacja uzyskanych efektów uczenia się: programowanie asynchroniczne, wdrożenia w środowisku Docker, konfiguracja serwerów oraz praca z systemem kontroli wersji Git.",
        sekcja_III="Uwagi i wnioski końcowe: praktyka przebiegła wzorowo, warunki pracy były bardzo dobre, a opiekun zakładowy służył fachową wiedzą techniczną przez cały okres jej trwania.",
        wersja=1, ocena=5.0 if status == 'Approved' else None, status=status)
    db.session.add(spr)
    db.session.commit()
    return spr


def _karta(praktyka, status='Approved'):
    kp = KartaPraktyki(praktyka_id=praktyka.id, ocena_param_zopz=5.0,
                       ocena_opisowa_zopz="Wzorowy praktykant, samodzielny i chętny do nauki.",
                       ocena_param_uopz=5.0, ocena_opisowa_uopz="Praktyka zaliczona na ocenę celującą.",
                       ocena_sprawozdania=5.0, status=status)
    db.session.add(kp)
    db.session.commit()
    return kp


def _ankieta(student, rok):
    ank = Ankieta(rok_akademicki=rok, kierunek=student.kierunek, forma_studiow=student.forma_studiow,
                  semestr=student.semestr, godziny=960, uwagi="Bardzo dobre praktyki, dużo się nauczyłem.")
    db.session.add(ank)
    db.session.commit()
    for q in range(1, 15):
        db.session.add(AnkietaOdpowiedz(ankieta_id=ank.id, pytanie_nr=q, odpowiedz=5))
    db.session.commit()
    return ank


def seed_demo_db():
    print("Starting demo database seeding...")

    from app.seed import seed_db
    seed_db()
    efekty = EfektUczenia.query.order_by(EfektUczenia.nr).all()

    # --- Użytkownicy ---
    uopz = _user("uopz@ans-elblag.pl", "Anna", "Nowak", "uopz", "uopz123")
    zopz1 = _user("zopz@ans-elblag.pl", "Adam", "Zopz", "zopz", "zopz123")
    zopz2 = _user("zopz2@ans-elblag.pl", "Marek", "Kowalski", "zopz", "zopz123")
    dyrektor = _user("dyrektor@ans-elblag.pl", "Jan", "Dyrektor", "dyrektor", "dyrektor123")

    su1 = _user("student1@ans-elblag.pl", "Kacper", "Student", "student", "student123")
    su2 = _user("student2@ans-elblag.pl", "Jan", "Kowalski", "student", "student123")
    su3 = _user("student3@ans-elblag.pl", "Michał", "Wiśniewski", "student", "student123")
    su4 = _user("student4@ans-elblag.pl", "Anna", "Lewandowska", "student", "student123")
    su5 = _user("student5@ans-elblag.pl", "Paweł", "Zieliński", "student", "student123")
    su6 = _user("student6@ans-elblag.pl", "Magda", "Wójcik", "student", "student123")
    su7 = _user("student7@ans-elblag.pl", "Karolina", "Nowicka", "student", "student123")

    s1 = _student(su1, "22334", "Informatyka", "Inżynieria Oprogramowania", 6, "stacjonarne", "2025/2026")
    s2 = _student(su2, "12345", "Informatyka", "Inżynieria Oprogramowania", 7, "stacjonarne", "2025/2026")
    s3 = _student(su3, "54321", "Informatyka", "Inżynieria Systemów", 6, "stacjonarne", "2025/2026")
    s4 = _student(su4, "33445", "Informatyka", "Inżynieria Oprogramowania", 7, "stacjonarne", "2025/2026")
    s5 = _student(su5, "44556", "Informatyka", "Inżynieria Systemów", 7, "stacjonarne", "2025/2026")
    s6 = _student(su6, "55667", "Informatyka", "Inżynieria Oprogramowania", 7, "niestacjonarne", "2025/2026")
    s7 = _student(su7, "66778", "Informatyka", "Inżynieria Oprogramowania", 7, "stacjonarne", "2025/2026")

    # --- Zakłady pracy ---
    zp1 = ZakladPracy.query.filter_by(nip="1234567890").first()
    if not zp1:
        zp1 = ZakladPracy(nazwa="SoftDev Sp. z o.o.", adres="Elbląg, ul. Grunwaldzka 12", nip="1234567890",
                          zopz_imie="Adam", zopz_nazwisko="Zopz", zopz_stanowisko="Senior Tech Lead",
                          zopz_wyksztalcenie="Wyższe magisterskie", status="Approved", zopz_uzytkownik_id=zopz1.id)
        db.session.add(zp1)
    zp2 = ZakladPracy.query.filter_by(nip="9876543210").first()
    if not zp2:
        zp2 = ZakladPracy(nazwa="Global IT Solutions", adres="Elbląg, ul. 1 Maja 45", nip="9876543210",
                          zopz_imie="Marek", zopz_nazwisko="Kowalski", zopz_stanowisko="Dyrektor IT",
                          zopz_wyksztalcenie="Wyższe", status="Approved", zopz_uzytkownik_id=zopz2.id)
        db.session.add(zp2)
    db.session.commit()

    def _praktyka(student, zaklad, termin_od, termin_do, status, **kw):
        existing = Praktyka.query.filter_by(student_id=student.id).first()
        if existing:
            return existing, False
        p = Praktyka(student_id=student.id, zaklad_id=zaklad.id, uopz_id=uopz.id,
                     termin_od=termin_od, termin_do=termin_do, rok_akademicki="2025/2026",
                     status=status, **kw)
        db.session.add(p)
        db.session.commit()
        return p, True

    # --- S1: zgłoszenie w edycji (Draft) + wniosek alternatywny dla dyrektora ---
    _praktyka(s1, zp1, date(2026, 7, 1), date(2026, 9, 30), "Draft")
    if not WniosekAlternatywny.query.filter_by(student_id=s1.id).first():
        wniosek = WniosekAlternatywny(
            student_id=s1.id, typ="praca_zawodowa",
            uzasadnienie="Pracuję jako Młodszy Programista na pełen etat od ponad roku. Zakres obowiązków pokrywa się z efektami uczenia się dla praktyki zawodowej.",
            status="Submitted")
        db.session.add(wniosek)
        db.session.commit()
        db.session.add(ZalacznikSkan(wniosek_id=wniosek.id, nazwa_pliku="umowa_o_prace.pdf",
                                     sciezka_pliku="uploads/alternative/umowa_o_prace.pdf",
                                     typ_dokumentu="umowa_o_prace"))
        db.session.commit()

    # --- S2: zgłoszenie złożone, czeka na weryfikację UOPZ (Submitted) ---
    _praktyka(s2, zp1, date(2026, 7, 1), date(2026, 9, 30), "Submitted")

    # --- S3: zgłoszenie odrzucone z komentarzem (Rejected) ---
    _praktyka(s3, zp2, date(2026, 7, 1), date(2026, 9, 30), "Rejected",
              komentarz_odrzucenia="Wybrany termin koliduje z sesją egzaminacyjną. Proszę uzgodnić nowy termin z zakładem i poprawić zgłoszenie.")

    # --- S4: praktyka w toku (Approved): harmonogram podpisany, dziennik częściowo, wpisy do podpisu przez ZOPZ ---
    p4, created4 = _praktyka(s4, zp1, date(2026, 4, 1), date(2026, 6, 30), "Approved")
    if created4:
        _harmonogram(p4, efekty, signatures=(1, 1, 1), status='Approved')
        _wpisy(p4, efekty, date(2026, 4, 1), n_approved=50, n_submitted=8)

    # --- S5: praktyka w toku, dziennik 120 dni do zatwierdzenia przez UOPZ + sprawozdanie do oceny ---
    p5, created5 = _praktyka(s5, zp2, date(2026, 3, 1), date(2026, 6, 30), "Approved")
    if created5:
        _harmonogram(p5, efekty, signatures=(1, 1, 1), status='Approved')
        _wpisy(p5, efekty, date(2026, 3, 1), n_approved=120)
        p5.dziennik_status = 'Under_Review'
        _sprawozdanie(p5, status='Submitted')
        db.session.commit()

    # --- S6: komplet dokumentacji złożony, finalna weryfikacja UOPZ (Under_Review) ---
    p6, created6 = _praktyka(s6, zp1, date(2025, 9, 1), date(2025, 12, 15), "Under_Review", ankieta_wypelniona=1)
    if created6:
        _harmonogram(p6, efekty, signatures=(1, 1, 1), status='Approved')
        _wpisy(p6, efekty, date(2025, 9, 1), n_approved=120)
        p6.dziennik_status = 'Closed'
        _efekty_potw(p6, efekty, status='Approved')
        _sprawozdanie(p6, status='Approved')
        _karta(p6, status='Approved')
        _ankieta(s6, "2025/2026")
        db.session.commit()

    # --- S7: praktyka rozliczona (Closed): egzamin zdany + wygenerowane dokumenty PDF ---
    p7, created7 = _praktyka(s7, zp2, date(2025, 2, 1), date(2025, 5, 30), "Closed",
                             ocena_koncowa=5.0, ankieta_wypelniona=1, dziennik_status="Closed")
    if created7:
        _harmonogram(p7, efekty, signatures=(1, 1, 1), status='Approved')
        _wpisy(p7, efekty, date(2025, 2, 1), n_approved=120)
        _efekty_potw(p7, efekty, status='Approved')
        _sprawozdanie(p7, status='Approved')
        _karta(p7, status='Closed')
        _ankieta(s7, "2025/2026")
        eg = Egzamin(praktyka_id=p7.id, termin=datetime(2025, 6, 15, 10, 0),
                     ocena_ustna=5.0, ocena_koncowa=5.0, status="Approved")
        db.session.add(eg)
        db.session.commit()
        db.session.add(KomisjaCzlonek(egzamin_id=eg.id, uzytkownik_id=uopz.id, rola_w_komisji="przewodniczacy"))
        db.session.add(KomisjaCzlonek(egzamin_id=eg.id, uzytkownik_id=dyrektor.id, rola_w_komisji="czlonek"))
        db.session.commit()

        # Wygeneruj dokumenty PDF, aby były pobieralne (rekordy Dokument + pliki)
        from app.routes.api.documents import generate_and_store
        for t in ['zal_nr2a', 'zal_nr3', 'zal_nr4', 'zal_nr6', 'zal_nr7', 'zal_nr8']:
            generate_and_store(p7, t)
        db.session.commit()

    print("Demo database seeding completed successfully.")
