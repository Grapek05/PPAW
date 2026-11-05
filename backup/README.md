# TaskBoard

System zarzadzania projektami i zadaniami rozwijany na laboratoriach przedmiotu
Podstawy programowania aplikacji webowych.

## Uruchomienie

API:

```bash
uv sync
uv run fastapi dev app/main.py
```

Frontend, w drugim terminalu:

```bash
uv run python -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

API: http://127.0.0.1:8000, frontend: http://127.0.0.1:5500

Frontend musi byc otwierany pod adresem `http://127.0.0.1:5500`. Ten origin jest
wpisany w konfiguracji CORS. Adres `http://localhost:5500` jest innym origin.

### Decyzje projektowe

- Zadanie należy do projektu. Relację wyraża filtr `GET /tasks?project_id=1`, a nie zagnieżdżenie `/projects/1/tasks`.
- Zadanie zmieniamy przez PATCH. PUT zostaje usunięty.
- Użytkownicy są tylko do odczytu. Tworzenie kont wymaga rejestracji (zajęcia 8).
- Tytuł zadania jest unikalny w obrębie projektu.
- Projektu z zadaniami nie można usunąć (409).
- Odwołanie w ciele żądania do nieistniejącego projektu lub użytkownika to 422, a nie 404.
- Wszystkie błędy mają format Problem Details (RFC 9457).


## Frontend

| Plik | Odpowiedzialnosc |
|---|---|
| `frontend/js/api.js` | komunikacja z API |
| `frontend/js/ui.js` | operacje na DOM |
| `frontend/js/main.js` | obsluga zdarzen, polaczenie obu modulow |

## Stan projektu

Po laboratorium 3: frontend w vanilla JavaScript pobiera, tworzy i usuwa zadania
przez Fetch API. Backend ma skonfigurowany CORS.

Dane sa przechowywane w pamieci procesu i znikaja po restarcie serwera.
Trwalosc danych zostanie dodana na zajeciach 6.
