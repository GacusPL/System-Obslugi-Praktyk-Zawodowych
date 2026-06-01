### Zadanie 3 — Flowchart: Logika uprawnień do edycji dokumentu

> Modeluje algorytm wykonywany przez backend przy każdej próbie edycji dokumentu. Pokrywa warunki z instrukcji: uwierzytelnienie, rola użytkownika, status dokumentu.

```mermaid
flowchart TD
    A([Użytkownik żąda edycji dokumentu]) --> B{Czy użytkownik\njest zalogowany?}

    B -- Nie --> C[/Przekieruj na stronę logowania\n HTTP 401/]
    C --> Z([Koniec])

    B -- Tak --> D{Jaka jest\nrola użytkownika?}

    D -- Admin --> E[/Udostępnij pełny\npodgląd i edycję/]
    E --> Z

    D -- Dyrektor --> E2{Czy dotyczy\nwniosku alternatywnego?}
    E2 -- Tak --> E3[/Udostępnij panel\ndecyzji wniosku/]
    E3 --> Z
    E2 -- Nie --> G

    D -- UOPZ lub ZOPZ --> F{Czy użytkownik jest\nprzypisany do tej praktyki?}
    F -- Nie --> G[/Zwróć błąd dostępu\nHTTP 403/]
    G --> Z
    F -- Tak --> H[/Udostępnij formularz\nkomentarza i decyzji/]
    H --> Z

    D -- Student --> I{Czy dokument\nnależy do studenta?}
    I -- Nie --> G

    I -- Tak --> J{Czy status dokumentu\nto 'Draft' lub 'Rejected'?}

    J -- Nie\nSubmitted / Under_Review\n/ Approved / Closed --> K[/Wyświetl dokument\nw trybie Read-only/]
    K --> Z

    J -- Tak --> L[/Udostępnij\nformularz edycji/]
    L --> Z
```
