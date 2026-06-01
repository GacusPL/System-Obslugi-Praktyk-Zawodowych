# ERD – System Obsługi Praktyk Zawodowych

Diagram encji wyprowadzony z załączników regulaminu praktyk (Zał. nr 2a, 3, 4, 4b, 5, 6, 7)
oraz logiki biznesowej zdefiniowanej w diagramach sekwencji (Procesy 1–9).

```mermaid
erDiagram
    UZYTKOWNIK {
        int id PK
        string imie
        string nazwisko
        string email UK
        string haslo_hash
        string rola
        datetime created_at
        datetime updated_at
    }

    STUDENT {
        int id PK
        int uzytkownik_id FK
        string nr_albumu UK
        string kierunek
        string specjalnosc
        int semestr
        string forma_studiow
        string rok_akademicki
    }

    ZAKLAD_PRACY {
        int id PK
        string nazwa
        string adres
        string nip UK
        string zopz_imie
        string zopz_nazwisko
        string zopz_stanowisko
        string zopz_wyksztalcenie
        string status
        datetime created_at
    }

    PRAKTYKA {
        int id PK
        int student_id FK
        int zaklad_id FK
        int uopz_id FK
        date termin_od
        date termin_do
        string rok_akademicki
        string status
        float ocena_koncowa
        bool ankieta_wypelniona
        string dziennik_status
        datetime created_at
        datetime updated_at
    }

    HARMONOGRAM {
        int id PK
        int praktyka_id FK
        bool podpis_student
        bool podpis_zopz
        bool podpis_uopz
        string status
        datetime created_at
        datetime updated_at
    }

    HARMONOGRAM_DZIAL {
        int id PK
        int harmonogram_id FK
        string nazwa_dzialu
        int planowane_dni
    }

    WPIS_DZIENNIKA {
        int id PK
        int praktyka_id FK
        int dzien_nr
        date data_wpisu
        text opis_prac
        string status
        text komentarz_zopz
        bool podpis_zopz
        datetime created_at
        datetime updated_at
    }

    WPIS_EFEKT {
        int id PK
        int wpis_id FK
        int efekt_id FK
    }

    EFEKT_UCZENIA {
        int id PK
        int nr
        text opis
    }

    POTWIERDZENIE_EFEKTOW {
        int id PK
        int praktyka_id FK
        int godziny_zrealizowane
        text opinia_uopz
        string status
        datetime created_at
        datetime updated_at
    }

    POTWIERDZENIE_EFEKT_OCENA {
        int id PK
        int potwierdzenie_id FK
        int efekt_id FK
        bool uzyskano
    }

    SPRAWOZDANIE {
        int id PK
        int praktyka_id FK
        text sekcja_I
        text sekcja_II
        text sekcja_III
        int wersja
        float ocena
        string status
        datetime created_at
        datetime updated_at
    }

    KARTA_PRAKTYKI {
        int id PK
        int praktyka_id FK
        float ocena_param_zopz
        text ocena_opisowa_zopz
        float ocena_param_uopz
        text ocena_opisowa_uopz
        float ocena_sprawozdania
        string status
        datetime created_at
        datetime updated_at
    }

    ANKIETA {
        int id PK
        string rok_akademicki
        string kierunek
        string forma_studiow
        int semestr
        int godziny
        text uwagi
        datetime created_at
    }

    ANKIETA_ODPOWIEDZ {
        int id PK
        int ankieta_id FK
        int pytanie_nr
        int odpowiedz
    }

    WNIOSEK_ALTERNATYWNY {
        int id PK
        int student_id FK
        string typ
        text uzasadnienie
        text opinia_komisji
        string decyzja
        string status
        datetime created_at
        datetime updated_at
    }

    ZALACZNIK_SKAN {
        int id PK
        int wniosek_id FK
        string nazwa_pliku
        string sciezka_pliku
        string typ_dokumentu
        datetime created_at
    }

    EGZAMIN {
        int id PK
        int praktyka_id FK
        datetime termin
        float ocena_ustna
        float ocena_koncowa
        string status
        datetime created_at
    }

    KOMISJA_CZLONEK {
        int id PK
        int egzamin_id FK
        int uzytkownik_id FK
        string rola_w_komisji
    }

    DOKUMENT {
        int id PK
        int praktyka_id FK
        string typ
        string sciezka_pliku
        string status
        datetime created_at
    }

    UZYTKOWNIK ||--o{ STUDENT : "jest"
    STUDENT ||--o{ PRAKTYKA : "odbywa"
    ZAKLAD_PRACY ||--o{ PRAKTYKA : "przyjmuje"
    UZYTKOWNIK ||--o{ PRAKTYKA : "nadzoruje jako UOPZ"
    PRAKTYKA ||--|| HARMONOGRAM : "ma"
    HARMONOGRAM ||--o{ HARMONOGRAM_DZIAL : "składa się z"
    PRAKTYKA ||--o{ WPIS_DZIENNIKA : "zawiera"
    WPIS_DZIENNIKA ||--o{ WPIS_EFEKT : "powiązany z"
    WPIS_EFEKT }o--|| EFEKT_UCZENIA : "odnosi się do"
    PRAKTYKA ||--|| POTWIERDZENIE_EFEKTOW : "ma"
    POTWIERDZENIE_EFEKTOW ||--o{ POTWIERDZENIE_EFEKT_OCENA : "ocenia"
    POTWIERDZENIE_EFEKT_OCENA }o--|| EFEKT_UCZENIA : "dotyczy"
    PRAKTYKA ||--o{ SPRAWOZDANIE : "ma"
    PRAKTYKA ||--|| KARTA_PRAKTYKI : "ma"
    STUDENT ||--o{ WNIOSEK_ALTERNATYWNY : "składa"
    WNIOSEK_ALTERNATYWNY ||--o{ ZALACZNIK_SKAN : "zawiera"
    PRAKTYKA ||--o{ EGZAMIN : "kończy się"
    EGZAMIN ||--o{ KOMISJA_CZLONEK : "składa się z"
    KOMISJA_CZLONEK }o--|| UZYTKOWNIK : "jest"
    PRAKTYKA ||--o{ DOKUMENT : "generuje"
    ANKIETA ||--o{ ANKIETA_ODPOWIEDZ : "zawiera"
```

## Uwagi projektowe

- Status dziennika praktyk nie jest osobną encją — wynika z agregacji statusów wpisów w WPIS_DZIENNIKA oraz statusu PRAKTYKA.
- Egzamin poprawkowy modelowany jest jako kolejny rekord w tabeli EGZAMIN (relacja 1:N z PRAKTYKA).
- Wynik egzaminu przechowywany jest bezpośrednio w polach tabeli EGZAMIN (ocena_ustna, ocena_koncowa).

## Legenda relacji

| Oznaczenie | Znaczenie |
|---|---|
| `\|\|--\|\|` | dokładnie jeden do dokładnie jednego (1:1) |
| `\|\|--o{` | dokładnie jeden do wielu (1:N) |
| `}o--\|\|` | wiele do dokładnie jednego (N:1) |

## Tabele pośrednie (relacje N:M)

- `WPIS_EFEKT` — jeden wpis dziennika może realizować wiele efektów uczenia się
- `POTWIERDZENIE_EFEKT_OCENA` — każdy z 13 efektów oceniany osobno per potwierdzenie
- `KOMISJA_CZLONEK` — wielu użytkowników może zasiadać w komisji egzaminacyjnej

## Dozwolone wartości statusów

| Tabela | Dozwolone statusy |
|---|---|
| `PRAKTYKA` | Draft, Submitted, Under_Review, Approved, Rejected, Closed |
| `HARMONOGRAM` | Draft, Submitted, Under_Review, Approved, Rejected |
| `WPIS_DZIENNIKA` | Draft, Submitted, Approved, Rejected |
| `POTWIERDZENIE_EFEKTOW` | Draft, Submitted, Under_Review, Approved, Rejected |
| `SPRAWOZDANIE` | Draft, Submitted, Under_Review, Approved, Rejected |
| `KARTA_PRAKTYKI` | Draft, Under_Review, Approved, Closed |
| `WNIOSEK_ALTERNATYWNY` | Submitted, Under_Review, Approved, Rejected |
| `EGZAMIN` | Draft, Approved, Rejected |
| `ZAKLAD_PRACY` | Approved, Rejected |
| `DOKUMENT` | Closed |