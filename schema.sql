-- =============================================================
-- System Obsługi Praktyk Zawodowych – IIS
-- Szkielet bazy danych SQLite
-- Wersja: 1.0 (prototyp)
-- =============================================================

PRAGMA foreign_keys = ON;

-- -------------------------------------------------------------
-- Słownik efektów uczenia się (13 efektów wg Zał. nr 2a i 4)
-- -------------------------------------------------------------
CREATE TABLE efekt_uczenia (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nr          INTEGER NOT NULL UNIQUE CHECK (nr BETWEEN 1 AND 13),
    opis        TEXT    NOT NULL
);

-- -------------------------------------------------------------
-- Użytkownicy systemu (wspólna tabela dla wszystkich ról)
-- -------------------------------------------------------------
CREATE TABLE uzytkownik (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    imie         TEXT    NOT NULL,
    nazwisko     TEXT    NOT NULL,
    email        TEXT    NOT NULL UNIQUE,
    haslo_hash   TEXT    NOT NULL,
    rola         TEXT    NOT NULL CHECK (rola IN (
                     'student', 'zopz', 'uopz',
                     'administrator', 'dyrektor'
                 )),
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- Studenci (rozszerzenie tabeli uzytkownik)
-- -------------------------------------------------------------
CREATE TABLE student (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    uzytkownik_id   INTEGER NOT NULL UNIQUE,
    nr_albumu       TEXT    NOT NULL UNIQUE,
    kierunek        TEXT    NOT NULL,
    specjalnosc     TEXT,
    semestr         INTEGER NOT NULL CHECK (semestr IN (6, 7)),
    forma_studiow   TEXT    NOT NULL CHECK (forma_studiow IN (
                        'stacjonarne', 'niestacjonarne'
                    )),
    rok_akademicki  TEXT    NOT NULL,
    FOREIGN KEY (uzytkownik_id) REFERENCES uzytkownik (id)
);

-- -------------------------------------------------------------
-- Zakłady pracy (§3 regulaminu – wymogi kwalifikacyjne ZOPZ)
-- -------------------------------------------------------------
CREATE TABLE zaklad_pracy (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    nazwa               TEXT    NOT NULL,
    adres               TEXT    NOT NULL,
    nip                 TEXT    NOT NULL UNIQUE,
    zopz_imie           TEXT    NOT NULL,
    zopz_nazwisko       TEXT    NOT NULL,
    zopz_stanowisko     TEXT    NOT NULL,
    zopz_wyksztalcenie  TEXT    NOT NULL,
    status              TEXT    NOT NULL DEFAULT 'Approved'
                            CHECK (status IN ('Approved', 'Rejected')),
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- Praktyki zawodowe (encja centralna systemu)
-- -------------------------------------------------------------
CREATE TABLE praktyka (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL,
    zaklad_id       INTEGER NOT NULL,
    uopz_id         INTEGER NOT NULL,
    termin_od       DATE    NOT NULL,
    termin_do       DATE    NOT NULL,
    rok_akademicki  TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'Draft'
                        CHECK (status IN (
                            'Draft', 'Submitted', 'Under_Review',
                            'Approved', 'Rejected', 'Closed'
                        )),
    ocena_koncowa   REAL    CHECK (ocena_koncowa BETWEEN 2.0 AND 5.0),
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student (id),
    FOREIGN KEY (zaklad_id)  REFERENCES zaklad_pracy (id),
    FOREIGN KEY (uopz_id)    REFERENCES uzytkownik (id)
);

-- -------------------------------------------------------------
-- Harmonogram praktyki (Zał. nr 2a – trzy podpisy)
-- -------------------------------------------------------------
CREATE TABLE harmonogram (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    praktyka_id     INTEGER NOT NULL UNIQUE,
    podpis_student  INTEGER NOT NULL DEFAULT 0 CHECK (podpis_student IN (0, 1)),
    podpis_zopz     INTEGER NOT NULL DEFAULT 0 CHECK (podpis_zopz IN (0, 1)),
    podpis_uopz     INTEGER NOT NULL DEFAULT 0 CHECK (podpis_uopz IN (0, 1)),
    status          TEXT    NOT NULL DEFAULT 'Draft'
                        CHECK (status IN (
                            'Draft', 'Submitted', 'Under_Review',
                            'Approved', 'Rejected'
                        )),
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (praktyka_id) REFERENCES praktyka (id)
);

-- -------------------------------------------------------------
-- Działy harmonogramu (podział 120 dni na komórki organizacyjne)
-- -------------------------------------------------------------
CREATE TABLE harmonogram_dzial (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    harmonogram_id  INTEGER NOT NULL,
    nazwa_dzialu    TEXT    NOT NULL,
    planowane_dni   INTEGER NOT NULL CHECK (planowane_dni > 0),
    FOREIGN KEY (harmonogram_id) REFERENCES harmonogram (id)
);

-- -------------------------------------------------------------
-- Wpisy dziennika praktyki (Zał. nr 6 – 120 dni roboczych)
-- -------------------------------------------------------------
CREATE TABLE wpis_dziennika (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    praktyka_id     INTEGER NOT NULL,
    dzien_nr        INTEGER NOT NULL CHECK (dzien_nr BETWEEN 1 AND 120),
    data_wpisu      DATE    NOT NULL,
    opis_prac       TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'Draft'
                        CHECK (status IN (
                            'Draft', 'Submitted', 'Approved', 'Rejected'
                        )),
    komentarz_zopz  TEXT,
    podpis_zopz     INTEGER NOT NULL DEFAULT 0 CHECK (podpis_zopz IN (0, 1)),
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (praktyka_id, dzien_nr),
    FOREIGN KEY (praktyka_id) REFERENCES praktyka (id)
);

-- -------------------------------------------------------------
-- Tabela pośrednia: wpis dziennika ↔ efekty uczenia się (N:M)
-- -------------------------------------------------------------
CREATE TABLE wpis_efekt (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    wpis_id     INTEGER NOT NULL,
    efekt_id    INTEGER NOT NULL,
    UNIQUE (wpis_id, efekt_id),
    FOREIGN KEY (wpis_id)   REFERENCES wpis_dziennika (id),
    FOREIGN KEY (efekt_id)  REFERENCES efekt_uczenia (id)
);

-- -------------------------------------------------------------
-- Potwierdzenie efektów uczenia się (Zał. nr 4)
-- -------------------------------------------------------------
CREATE TABLE potwierdzenie_efektow (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    praktyka_id             INTEGER NOT NULL UNIQUE,
    godziny_zrealizowane    INTEGER NOT NULL CHECK (godziny_zrealizowane > 0),
    opinia_uopz             TEXT,
    status                  TEXT    NOT NULL DEFAULT 'Draft'
                                CHECK (status IN (
                                    'Draft', 'Submitted', 'Under_Review',
                                    'Approved', 'Rejected'
                                )),
    created_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (praktyka_id) REFERENCES praktyka (id)
);

-- -------------------------------------------------------------
-- Tabela pośrednia: potwierdzenie ↔ efekty (ocena każdego z 13)
-- -------------------------------------------------------------
CREATE TABLE potwierdzenie_efekt_ocena (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    potwierdzenie_id    INTEGER NOT NULL,
    efekt_id            INTEGER NOT NULL,
    uzyskano            INTEGER NOT NULL CHECK (uzyskano IN (0, 1)),
    UNIQUE (potwierdzenie_id, efekt_id),
    FOREIGN KEY (potwierdzenie_id) REFERENCES potwierdzenie_efektow (id),
    FOREIGN KEY (efekt_id)         REFERENCES efekt_uczenia (id)
);

-- -------------------------------------------------------------
-- Sprawozdanie studenta (Zał. nr 7 – trzy sekcje + wersjonowanie)
-- -------------------------------------------------------------
CREATE TABLE sprawozdanie (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    praktyka_id     INTEGER NOT NULL,
    sekcja_I        TEXT    NOT NULL,
    sekcja_II       TEXT    NOT NULL,
    sekcja_III      TEXT    NOT NULL,
    wersja          INTEGER NOT NULL DEFAULT 1,
    ocena           REAL    CHECK (ocena BETWEEN 2.0 AND 5.0),
    status          TEXT    NOT NULL DEFAULT 'Draft'
                        CHECK (status IN (
                            'Draft', 'Submitted', 'Under_Review',
                            'Approved', 'Rejected'
                        )),
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (praktyka_id) REFERENCES praktyka (id)
);

-- -------------------------------------------------------------
-- Karta praktyki zawodowej (Zał. nr 3 – oceny ZOPZ i UOPZ)
-- -------------------------------------------------------------
CREATE TABLE karta_praktyki (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    praktyka_id         INTEGER NOT NULL UNIQUE,
    ocena_param_zopz    REAL    CHECK (ocena_param_zopz BETWEEN 2.0 AND 5.0),
    ocena_opisowa_zopz  TEXT,
    ocena_param_uopz    REAL    CHECK (ocena_param_uopz BETWEEN 2.0 AND 5.0),
    ocena_opisowa_uopz  TEXT,
    ocena_sprawozdania  REAL    CHECK (ocena_sprawozdania BETWEEN 2.0 AND 5.0),
    status              TEXT    NOT NULL DEFAULT 'Draft'
                            CHECK (status IN (
                                'Draft', 'Under_Review',
                                'Approved', 'Closed'
                            )),
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (praktyka_id) REFERENCES praktyka (id)
);

-- -------------------------------------------------------------
-- Ankieta ewaluacyjna (Zał. nr 5 – anonimowa, brak student_id)
-- -------------------------------------------------------------
CREATE TABLE ankieta (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    rok_akademicki  TEXT    NOT NULL,
    kierunek        TEXT    NOT NULL,
    forma_studiow   TEXT    NOT NULL,
    semestr         INTEGER NOT NULL,
    godziny         INTEGER NOT NULL,
    uwagi           TEXT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------
-- Odpowiedzi ankiety (14 pytań, skala 1–5)
-- -------------------------------------------------------------
CREATE TABLE ankieta_odpowiedz (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ankieta_id  INTEGER NOT NULL,
    pytanie_nr  INTEGER NOT NULL CHECK (pytanie_nr BETWEEN 1 AND 14),
    odpowiedz   INTEGER NOT NULL CHECK (odpowiedz BETWEEN 1 AND 5),
    UNIQUE (ankieta_id, pytanie_nr),
    FOREIGN KEY (ankieta_id) REFERENCES ankieta (id)
);

-- -------------------------------------------------------------
-- Wniosek o zaliczenie alternatywne (Zał. nr 4b – §4 regulaminu)
-- -------------------------------------------------------------
CREATE TABLE wniosek_alternatywny (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL,
    typ             TEXT    NOT NULL CHECK (typ IN (
                        'praca_zawodowa', 'staz', 'dzialalnosc_gospodarcza'
                    )),
    uzasadnienie    TEXT    NOT NULL,
    opinia_komisji  TEXT,
    decyzja         TEXT    CHECK (decyzja IN (
                        'zgoda_pelna', 'zgoda_czesciowa', 'odmowa'
                    )),
    status          TEXT    NOT NULL DEFAULT 'Submitted'
                        CHECK (status IN (
                            'Submitted', 'Under_Review',
                            'Approved', 'Rejected'
                        )),
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES student (id)
);

-- -------------------------------------------------------------
-- Egzamin z praktyki (§4 pkt 5-10 regulaminu)
-- -------------------------------------------------------------
CREATE TABLE egzamin (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    praktyka_id     INTEGER NOT NULL,
    termin          DATETIME NOT NULL,
    ocena_ustna     REAL    CHECK (ocena_ustna BETWEEN 2.0 AND 5.0),
    ocena_koncowa   REAL    CHECK (ocena_koncowa BETWEEN 2.0 AND 5.0),
    status          TEXT    NOT NULL DEFAULT 'Draft'
                        CHECK (status IN (
                            'Draft', 'Approved', 'Rejected'
                        )),
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (praktyka_id) REFERENCES praktyka (id)
);

-- -------------------------------------------------------------
-- Tabela pośrednia: egzamin ↔ członkowie komisji (N:M)
-- -------------------------------------------------------------
CREATE TABLE komisja_czlonek (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    egzamin_id      INTEGER NOT NULL,
    uzytkownik_id   INTEGER NOT NULL,
    rola_w_komisji  TEXT    NOT NULL CHECK (rola_w_komisji IN (
                        'przewodniczacy', 'czlonek'
                    )),
    UNIQUE (egzamin_id, uzytkownik_id),
    FOREIGN KEY (egzamin_id)    REFERENCES egzamin (id),
    FOREIGN KEY (uzytkownik_id) REFERENCES uzytkownik (id)
);

-- -------------------------------------------------------------
-- Wygenerowane dokumenty PDF (archiwum e-teczki)
-- -------------------------------------------------------------
CREATE TABLE dokument (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    praktyka_id     INTEGER,
    typ             TEXT    NOT NULL CHECK (typ IN (
                        'zal_nr2a', 'zal_nr3', 'zal_nr4',
                        'zal_nr4b', 'zal_nr5', 'zal_nr6',
                        'zal_nr7', 'zal_nr8'
                    )),
    sciezka_pliku   TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'Closed',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (praktyka_id) REFERENCES praktyka (id)
);