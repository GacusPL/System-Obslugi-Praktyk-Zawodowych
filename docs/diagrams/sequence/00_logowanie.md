### Proces 0 — Uwierzytelnianie przez Microsoft OAuth2
> Logowanie do systemu odbywa się wyłącznie przez konto Microsoft (Azure AD). Przy pierwszym logowaniu system tworzy konto użytkownika i wymaga przypisania roli przez Administratora.

```mermaid
sequenceDiagram
    actor U as Użytkownik
    participant FE as Frontend
    participant FB as Flask_Backend
    participant MS as Microsoft_OAuth2
    participant DB as Database

    U->>FE: Kliknij "Zaloguj przez Microsoft"
    FE->>FB: GET /auth/login
    FB->>MS: Redirect do Microsoft login (client_id, scope, redirect_uri)
    MS-->>U: Formularz logowania Microsoft
    U->>MS: Wprowadza dane (email uczelniane)
    MS->>FB: Callback z authorization code
    FB->>MS: POST /token {code, client_secret}
    MS-->>FB: access_token + id_token
    FB->>MS: GET /me (Bearer token)
    MS-->>FB: {email, imie, nazwisko}

    FB->>DB: SELECT uzytkownik WHERE email = ?
    DB-->>FB: użytkownik / null

    alt Pierwsze logowanie (brak konta)
        FB->>DB: INSERT uzytkownik {email, imie, nazwisko, rola: null}
        DB-->>FB: uzytkownik_id
        FB->>FE: Przekieruj do strony oczekiwania na aktywację
        FE-->>U: Konto utworzone, oczekuje na przypisanie roli przez Administratora

        Note over FB,DB: Administrator przypisuje rolę w panelu administracyjnym
    else Konto istnieje, rola przypisana
        FB->>FB: Flask-Login: login_user(uzytkownik)
        FB->>DB: UPDATE uzytkownik {updated_at: now()}
        FB-->>FE: Redirect do dashboard
        FE-->>U: Panel główny (widok zależny od roli)
    else Konto istnieje, brak roli
        FB-->>FE: Przekieruj do strony oczekiwania
        FE-->>U: Konto oczekuje na aktywację
    end
```

> **Uwaga:** System korzysta z Flask-Login do zarządzania sesjami (`login_user`, `logout_user`, `@login_required`). Rola użytkownika determinuje dostępne widoki i uprawnienia zgodnie z flowchartem logiki uprawnień.
