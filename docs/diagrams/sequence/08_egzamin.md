### Proces 8 — Egzamin ustny i eksport ocen
> Dane: Regulamin §4 pkt 5–10 (egzamin przed Komisją, protokół Zał. nr 8), Zał. nr 3 (oceny cząstkowe ZOPZ i UOPZ 2–5), ocena sprawozdania 2–5. Eksport do CSV/XLSX z kolumnami nr albumu, nazwisko, imię, ocena końcowa, data.

```mermaid
sequenceDiagram
    actor S as Student
    actor UOPZ as Opiekun_Uczeln
    actor Urz as Urzednik
    participant FE as Frontend
    participant FB as Flask_Backend
    participant J as JSON_Database
    participant PDF as Generator_PDF

    Urz->>FE: Ustawia termin egzaminu i skład komisji
    FE->>FB: POST /egzamin {praktyka_id, data_termin, komisja_sklad[]}
    FB->>J: INSERT egzamin {status: "Draft"}
    FB->>S: Powiadomienie e-mail: termin egzaminu
    FB->>UOPZ: Powiadomienie: termin egzaminu

    S->>FE: Sprawdza termin
    FE->>FB: GET /egzamin/{id}
    FB->>J: SELECT egzamin + dokumentacja_studenta
    J-->>FB: dane
    FB-->>FE: karta egzaminu ze statusem dokumentacji

    Urz->>FE: Otwiera protokół egzaminacyjny (Zał. nr 8)
    FE->>FB: GET /egzamin/{id}/protokol
    FB->>J: SELECT oceny cząstkowe (ZOPZ 2-5, UOPZ 2-5, sprawozdanie 2-5)
    J-->>FB: oceny cząstkowe
    FB-->>FE: formularz protokołu z ocenami cząstkowymi

    Urz->>FE: Wpisuje ocenę z egzaminu ustnego (2–5) i ocenę końcową
    FE->>FB: POST /egzamin/{id}/wynik {ocena_ustna, ocena_koncowa}
    FB->>J: Walidacja: ocena w zakresie 2–5
    J-->>FB: OK / błąd zakresu

    alt Ocena niedostateczna (2)
        FB->>J: UPDATE egzamin {status: "Rejected"}
        FB->>J: INSERT termin_poprawkowy
        FB->>S: Powiadomienie: egzamin niezdany, wyznaczono poprawkę
    else Ocena pozytywna (3–5)
        FB->>J: INSERT wynik_egzaminu {ocena_koncowa, data}
        FB->>J: UPDATE praktyka {status: "Closed", ocena_koncowa}
        J-->>FB: OK

        FB->>J: SELECT student, komisja, oceny_cząstkowe, ocena_koncowa, data
        J-->>FB: komplet danych
        FB->>PDF: render_protokol_egzaminu(dane)
        PDF-->>FB: protokol_zal8.pdf
        FB->>J: INSERT dokument {typ: "protokol_zal8", status: "Closed"}
        J-->>FB: OK
        FB-->>FE: Protokół gotowy
        FE-->>Urz: Pobierz protokół (Zał. nr 8)
        FE-->>S: Powiadomienie: praktyka zaliczona

        Note over Urz,J: Eksport ocen do CSV/XLSX
        Urz->>FE: Kliknij "Eksportuj oceny" (filtr: semestr, rok akademicki)
        FE->>FB: GET /eksport/oceny?rok_ak=2024/2025&format=xlsx
        FB->>J: SELECT nr_albumu, nazwisko, imie, ocena_koncowa, data_zaliczenia FROM praktyki WHERE rok_ak=? AND status="Closed"
        J-->>FB: lista ocen
        FB->>FB: Generuj plik XLSX (openpyxl) lub CSV
        FB-->>FE: oceny_praktyki_2024_2025.xlsx
        FE-->>Urz: Pobierz plik do ręcznego wpisu w USOS
    end
```
