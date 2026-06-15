# System Obsługi Praktyk Zawodowych (SOPZ) — ANS Elbląg

System cyfryzacji i kompleksowego zarządzania obiegiem dokumentacji praktyk zawodowych w Instytucie Informatyki Stosowanej Akademii Nauk Stosowanych w Elblągu.

---

## 1. Opis projektu
SOPZ automatyzuje cały proces obsługi praktyk studenckich (wymiar 120 dni / 960 godzin): od rejestracji praktyki, przez codzienne prowadzenie dziennika praktyk z powiązaniem do 13 efektów uczenia się, po trójstronne podpisywanie harmonogramu, sprawozdanie końcowe, anonimową ankietę ewaluacyjną, weryfikację dokumentacji przez Uczelnianego Opiekuna Praktyk Zawodowych (UOPZ), egzamin dyplomowy i eksport ocen do systemu USOS. Obsługuje również ścieżkę alternatywną (wniosek 4b o zaliczenie na podstawie pracy zawodowej / własnej działalności).

---

## 2. Stack technologiczny

| Warstwa | Technologia |
|---|---|
| **Backend** | Python 3.11+ / Flask 3.0 |
| **Baza danych (Prototyp / Dev)** | SQLite |
| **Baza danych (Produkcja / Docker)** | MariaDB 10.11 |
| **Uwierzytelnianie** | Microsoft Entra ID (Azure AD) via MSAL + Flask-Login |
| **Frontend** | HTML5 / Vanilla CSS / JavaScript (Vanilla) + HTMX |
| **Generowanie PDF** | ReportLab (programmatic, z obsługą polskich znaków) |
| **Rate Limiter** | Flask-Limiter |
| **Zarządzanie migracjami** | Flask-Migrate / Alembic |
| **Konteneryzacja** | Docker & Docker Compose |

---

## 3. Wymagania systemowe
- **Lokalnie**:
  - Python 3.11 lub nowszy
  - SQLite 3
- **Kontenery**:
  - Docker 20.10+
  - Docker Compose v2.0+

---

## 4. Uruchomienie lokalne

### Krok 1: Klonowanie i przygotowanie środowiska
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
pip install -r requirements.txt
```

### Krok 2: Konfiguracja zmiennych środowiskowych
Utwórz plik `.env` w katalogu głównym projektu na podstawie `.env.example`:
```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=dev_secret_key_random
E2E=False

# Konfiguracja Microsoft OAuth
MICROSOFT_CLIENT_ID=twoj-client-id
MICROSOFT_CLIENT_SECRET=twoj-client-secret
MICROSOFT_TENANT_ID=twoj-tenant-id
MICROSOFT_REDIRECT_URI=http://localhost:5000/auth/callback
MICROSOFT_AUTHORITY=https://login.microsoftonline.com/twoj-tenant-id
```

### Krok 3: Inicjalizacja bazy danych i seedowanie danych testowych
```bash
flask db upgrade

# Opcja A: Podstawowy seed (tylko efekty uczenia się i admin)
flask seed

# Opcja B: Pełny seed demonstracyjny (efekty, studenci, dzienniki, wpisy itp.)
flask seed-demo
```

### Krok 4: Uruchomienie aplikacji
```bash
flask run --port=5000
```
Aplikacja będzie dostępna pod adresem: [http://localhost:5000](http://localhost:5000)

---

## 5. Uruchomienie w kontenerach (Docker)

Docker Compose automatycznie orkiestruje 3 kontenery w izolowanej sieci `backend`.

```bash
# Uruchomienie w tle
docker-compose up -d --build
```
Dzięki skryptowi `docker-entrypoint.sh` aplikacja automatycznie poczeka na gotowość bazy MariaDB, przeprowadzi migracje bazy danych, wgra dane testowe (seed) i uruchomi serwer produkcyjny Gunicorn na porcie `80`.

Aplikacja będzie dostępna pod adresem: [http://localhost](http://localhost)

### Podział i Architektura Kontenerów

Aplikacja jest podzielona na trzy dedykowane serwisy kontenerowe:

```mermaid
graph TD
    Client["Przeglądarka (Klient)"] -->|Port 80 HTTP / 443 HTTPS| Nginx["Serwer Nginx (nginx)"]
    Nginx -->|Bezpośrednie serwowanie| StaticVolume[("Wolumen: static_files")]
    Nginx -->|Przekierowanie proxy (Port 8000)| Gunicorn["Aplikacja Flask/Gunicorn (web)"]
    Gunicorn -->|Połączenie SQL (Port 3306)| DB["Baza MariaDB (db)"]
    DB -->|Persystencja danych| DBVolume[("Wolumen: db_data")]
    Gunicorn -->|Zapis dokumentów PDF| PDFVolume[("Wolumen: generated_docs")]
```

1. **`db` (MariaDB 10.11)**:
   - **Rola**: Produkcyjna baza danych przechowująca wszystkie rekordy (użytkownicy, praktyki, dzienniki, oceny).
   - **Wolumeny**: `db_data` mapowany na `/var/lib/mysql` gwarantuje, że dane nie zostaną utracone po restarcie kontenerów.
   - **Healthcheck**: Skrypt `healthcheck.sh` co 10s sprawdza gotowość silnika InnoDB przed wpuszczeniem połączeń z aplikacji.

2. **`web` (Aplikacja Flask + Gunicorn)**:
   - **Rola**: Backend serwera realizujący logikę biznesową, autoryzację oraz generowanie PDF.
   - **Konfiguracja**: Gunicorn uruchamia 4 procesy robocze (workers) obsługujące ruch na porcie 8000 z timeoutem 120s (dla generowania dużych PDF).
   - **Inicjalizacja**: Skrypt `docker-entrypoint.sh` wstrzymuje uruchomienie serwera WWW do momentu, gdy kontener bazy danych zgłosi pełną gotowość. Następnie wykonuje automatycznie `flask db upgrade` i seeduje początkowe dane.

3. **`nginx` (Reverse Proxy & Static Web Server)**:
   - **Rola**: Punkt wejściowy do systemu. Odciąża aplikację Flask i podnosi bezpieczeństwo.
   - **Funkcje**:
     - **Serwowanie plików statycznych**: Zapytania do `/static/` są obsługiwane bezpośrednio z dysku (wolumen `static_files`) z pominięciem Flaska, co drastycznie zwiększa wydajność.
     - **Nagłówki Bezpieczeństwa**: Wstrzykuje nagłówki HSTS, CSP, X-Frame-Options, nosniff.
     - **Rate Limiting**: Ogranicza liczbę żądań na sekundę (`limit_req_zone`) zapobiegając atakom DoS.

---

## 6. Tabela zmiennych środowiskowych

| Nazwa zmiennej | Opis | Domyślna wartość | Środowisko |
|---|---|---|---|
| `FLASK_ENV` | Środowisko uruchomieniowe (`development`, `production`) | `development` | Wszystkie |
| `SECRET_KEY` | Klucz szyfrujący sesje Flask | `default-key` | Produkcja (wymagany silny) |
| `DATABASE_URL` | URI połączenia z bazą danych | SQLite (lokalnie) | Produkcja (MariaDB) |
| `MICROSOFT_CLIENT_ID` | Identyfikator aplikacji Microsoft Entra ID | Brak | Wszystkie |
| `MICROSOFT_CLIENT_SECRET` | Klucz aplikacji Microsoft Entra ID | Brak | Wszystkie |
| `MICROSOFT_TENANT_ID` | GUID dzierżawy Azure AD | Brak | Wszystkie |
| `MICROSOFT_REDIRECT_URI` | Adres URL callback logowania | Brak | Wszystkie |

---

## 7. Struktura projektu

```
├── app/
│   ├── routes/              # Kontrolery i trasy (Web + API v1)
│   │   ├── api/             # API REST endpoints (P1-P9)
│   │   ├── auth.py          # Logowanie Microsoft OAuth
│   │   └── main.py          # Główne widoki dashboardów
│   ├── templates/           # Szablony Jinja2 + Bootstrap 5
│   ├── static/              # CSS, JS, obrazy
│   ├── pdf/                 # Moduł generowania 8 załączników PDF
│   ├── models.py            # Definicje modeli bazodanowych SQLAlchemy
│   ├── validators.py        # Logika walidacji biznesowej
│   ├── decorators.py        # Dekoratory ról użytkowników
│   └── logging_config.py    # Rotacja logów do plików logs/
├── instance/                # Instancja bazy SQLite (lokalnie)
├── migrations/              # Skrypty migracji bazy danych Alembic
├── nginx/                   # Konfiguracja serwera Nginx (Dockerfile + nginx.conf)
├── tests/                   # Testy automatyczne (Unit + E2E Playwright)
│   ├── e2e/                 # Testy scenariuszy Playwright
│   └── conftest.py          # Konfiguracja testów pytest
├── Dockerfile               # Wieloetapowy obraz Flask
├── docker-compose.yml       # Orkiestracja kontenerów
├── docker-entrypoint.sh     # Skrypt startowy kontenera Web
├── gunicorn.conf.py         # Konfiguracja produkcyjna WSGI
├── requirements.txt         # Zależności Pythona
├── SECURITY_AUDIT.md        # Wynik audytu bezpieczeństwa OWASP
└── IMPLEMENTATION_PLAN.md   # Szczegółowy plan wdrożenia
```

---

## 8. Wykaz kluczowych endpointów API (v1)

| Metoda | Endpoint | Rola | Opis |
|---|---|---|---|
| `POST` | `/api/v1/praktyki` | Student | Zgłoszenie nowej praktyki (Draft) |
| `PATCH` | `/api/v1/praktyki/<id>` | UOPZ/ZOPZ | Zmiana statusu praktyki (proces akceptacji) |
| `POST` | `/api/v1/harmonogramy` | UOPZ | Tworzenie harmonogramu (120 dni) |
| `POST` | `/api/v1/dziennik/wpisy` | Student | Dodanie wpisu do dziennika (dni 1-120) |
| `PATCH` | `/api/v1/dziennik/wpisy/<id>` | ZOPZ | Akceptacja/odrzucenie wpisu w dzienniku |
| `POST` | `/api/v1/efekty/potwierdzenie` | ZOPZ | Ocena 13 efektów uczenia się |
| `POST` | `/api/v1/sprawozdanie` | Student | Złożenie sprawozdania z praktyki |
| `POST` | `/api/v1/ankieta` | Student | Złożenie anonimowej ankiety (14 pytań) |
| `POST` | `/api/v1/dokumentacja/zloz` | Student | Złożenie kompletu dokumentów (P6) |
| `GET` | `/api/v1/documents/<id>/download` | Wszyscy (Owner) | Pobranie wygenerowanego archiwum PDF |
| `GET` | `/api/v1/eksport/oceny` | Admin | Eksport ocen końcowych do USOS (XLSX) |

---

## 9. Testowanie automatyczne

Aplikacja posiada pełny pakiet testowy obejmujący testy jednostkowe modeli, tras, walidatorów oraz testy integracyjne E2E z użyciem Playwright.

```bash
# Uruchomienie wszystkich testów
python -m pytest

# Testy z pokryciem kodu
python -m pytest --cov=app --cov-report=term-missing
```

---

## 10. Aktorzy i role w systemie

1. **Student** — uzupełnia profil, wnioskuje o praktykę, prowadzi dziennik (120 dni), składa sprawozdanie, wypełnia anonimową ankietę, pobiera zatwierdzone PDF.
2. **Zakładowy Opiekun Praktyki (ZOPZ)** — podpisuje harmonogram, weryfikuje wpisy dzienne, potwierdza 13 efektów uczenia się, wystawia ocenę końcową z praktyki.
3. **Uczelniany Opiekun Praktyk (UOPZ)** — weryfikuje zgłoszenia, nadzoruje realizację harmonogramu, ocenia sprawozdanie, zatwierdza komplet dokumentacji praktykanta.
4. **Dyrektor Instytutu (Dyrektor)** — rozpatruje wnioski o ścieżkę alternatywną (zaliczenie na podstawie pracy/firmy).
5. **Administrator** — konfiguracja kont użytkowników, przypisywanie opiekunów, zarządzanie bazą zakładów pracy, eksport ocen do USOS.

---

## 11. Resetowanie bazy danych i migracji

### Ponowna inicjalizacja i seedowanie
W aktywowanym środowisku wirtualnym (`venv`) uruchom:
```bash
# Inicjalizacja repozytorium migracji
flask db init

# Wygenerowanie nowej migracji początkowej
flask db migrate -m "Initial migration"

# Zaaplikowanie migracji do nowej bazy
flask db upgrade

# Wgranie danych (seed) - podstawowy lub demonstracyjny:
flask seed       # podstawowy seed
# LUB
flask seed-demo  # pełny seed demonstracyjny (użytkownicy, dzienniki itp.)
```

