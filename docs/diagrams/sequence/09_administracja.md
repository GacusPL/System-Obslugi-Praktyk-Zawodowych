### Proces 9 — Administracja systemu
> Dane: Regulamin §2–3, §8 (porozumienia z zakładami, kwalifikacje ZOPZ, przypisanie opiekunów, obsługa wyjątków: przedłużenia do 1 miesiąca §6, przesunięcia terminu, studia zagraniczne).

```mermaid
sequenceDiagram
    actor Adm as Admin
    actor UOPZ as Opiekun_Uczeln
    participant FE as Frontend
    participant FB as Flask_Backend
    participant J as JSON_Database

    Note over Adm,J: Zarządzanie zakładami pracy i porozumieniami (§2)
    Adm->>FE: Dodaje nowy zakład pracy + dane ZOPZ
    FE->>FB: POST /zaklady {nazwa, adres, nip, zopz_imie, zopz_stanowisko, wyksztalcenie}
    FB->>J: Walidacja: ZOPZ spełnia wymogi §3 pkt 3 (wykształcenie wyższe IT)
    J-->>FB: OK / błąd kwalifikacji

    alt ZOPZ nie spełnia wymagań
        FB-->>FE: 422 + komunikat o wymaganiach §3
        FE-->>Adm: Wyświetl wymagane kwalifikacje
    else ZOPZ spełnia wymagania
        FB->>J: INSERT zakład_pracy {status: "Approved"}
        J-->>FB: zaklad_id
        FB-->>FE: Zakład dodany pomyślnie
    end

    Note over Adm,J: Przypisanie opiekunów do studentów
    Adm->>FE: Przypisuje UOPZ do grupy studentów
    FE->>FB: POST /przypisania {uopz_id, studenci_ids[]}
    FB->>J: INSERT przypisania_opiekunow
    J-->>FB: OK
    FB-->>FE: Przypisania zapisane

    Note over UOPZ,J: Obsługa wyjątku – przedłużenie praktyki (§6 pkt 2-3)
    UOPZ->>FE: Rejestruje wniosek o przedłużenie (choroba powyżej 40h)
    FE->>FB: POST /przedluzenie {praktyka_id, powod, liczba_dni, nowa_data_konca}
    FB->>J: Walidacja: max 1 miesiąc po planowanym zakończeniu (§6 pkt 3)
    J-->>FB: OK / przekroczony limit

    alt Przekroczony limit 1 miesiąca
        FB-->>FE: 422 + komunikat o limicie
        FE-->>UOPZ: Wymagana osobna decyzja Dyrektora IIS
    else Przedłużenie w dopuszczalnym zakresie
        FB->>J: UPDATE praktyka {data_konca: nowa, status: "Under_Review"}
        J-->>FB: OK
        FB-->>FE: Przedłużenie zapisane
    end

    Note over Adm,J: Raport zbiorczy i eksport
    Adm->>FE: Żąda raportu (filtr: rok akademicki, semestr)
    FE->>FB: GET /raporty/stan-praktyk?rok_ak=2024/2025
    FB->>J: SELECT COUNT(*) GROUP BY status FROM praktyki WHERE rok_ak=?
    J-->>FB: statystyki (Approved, Submitted, Closed, Rejected)
    FB-->>FE: dashboard z podsumowaniem
    FE-->>Adm: Wyświetl raport zbiorczy

    Adm->>FE: Kliknij "Eksportuj raport"
    FE->>FB: GET /raporty/eksport?rok_ak=2024/2025&format=csv
    FB->>J: SELECT pelne dane wszystkich praktyk
    J-->>FB: dane
    FB->>FB: Generuj raport_praktyki_2024_2025.csv
    FB-->>FE: raport_praktyki_2024_2025.csv
    FE-->>Adm: Pobierz plik CSV
```
