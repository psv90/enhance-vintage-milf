# Rejestr błędów - Enhance Vintage Milf

## 2026-11-15 · Pasek postępu stał w miejscu, gdy krok trwał dłużej niż szacunek
- **Status:** naprawiony
- **Gdzie:** aplikacja.py:postep()
- **Objaw:** w kroku 1 pasek dochodził do 57% i stał, a „zostało” rosło, dopóki krok się nie skończył.
- **Przyczyna:** postęp kroku liczony liniowo z szacowanego czasu i ucięty na 95%.
- **Naprawa:** krzywa nasycenia 1 - e^(-1,2·t/szacunek), ucięta na 97%: przy szacowanym czasie ok. 70%, potem coraz wolniej, ale zawsze się rusza.

## 2026-11-15 · Upuszczony do okna film nie ma ścieżki
- **Status:** porzucony (ograniczenie przeglądarki)
- **Gdzie:** ui/app.js (zdarzenie drop)
- **Objaw:** po upuszczeniu filmu na okno programu nie da się go poprawić w miejscu.
- **Przyczyna:** okno przeglądarki nie dostaje pełnej ścieżki upuszczonego pliku, a wynik ma powstać obok oryginału.
- **Naprawa:** okno pokazuje podpowiedź; filmy upuszcza się na skrót albo na `Enhance Vintage Milf.cmd` (trafiają do kolejki działającego okna).
