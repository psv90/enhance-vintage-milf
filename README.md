# Poprawa wideo

Poprawia stare, małe filmy jednym kliknięciem:

1. powiększa obraz 4 razy (RelayVSR, sztuczna inteligencja),
2. wyrównuje kolory i biel osobno w każdej scenie, poprawia kontrast, lekko odszumia i wyostrza,
3. podnosi płynność do 60 albo 120 klatek na sekundę (RIFE),
4. robi film porównawczy przed/po.

Wyniki zapisuje obok oryginału: `<film>_poprawiony_120fps.mp4` i `<film>_porownanie_120fps.mp4`.

## Wymagania

- Windows 10 albo 11, 64-bit.
- Karta graficzna NVIDIA z aktualnym sterownikiem. Sprawdzone na RTX 5070 Ti (16 GB); na kartach z mniejszą pamięcią może nie działać.
- Około 20 GB wolnego miejsca na dysku, na którym leży ten folder.
- Internet przy pierwszym uruchomieniu.

## Jak używać

1. Pobierz paczkę (na GitHubie: zielony przycisk **Code** → **Download ZIP**) i rozpakuj ją w dowolne miejsce, najlepiej na dysk z dużą ilością miejsca.
2. Kliknij dwa razy `Popraw wideo.cmd`.
3. Za pierwszym razem instalator sam pobierze wszystko do folderu `silnik` (Python, PyTorch, RelayVSR, modele, w razie potrzeby ffmpeg). Trwa to od kilkunastu minut do godziny. Jeśli przerwie się w połowie, uruchom ponownie - dokończy.
4. Wybierz film i liczbę klatek na sekundę. Po skończeniu otworzy się folder z wynikiem.

Po instalacji obok pojawi się skrót `Popraw wideo` z ikoną. Film można też przeciągnąć myszką na skrót albo na `Popraw wideo.cmd`.

Program nic nie instaluje poza tym folderem. Żeby go usunąć, wystarczy skasować folder.

## Czas

Film 34 s w rozdzielczości 480x360 liczy się około 10 minut na RTX 5070 Ti. Gdy w tle działa inny program używający karty (np. ComfyUI, gry), może to trwać wielokrotnie dłużej.

## Licencje

- RelayVSR: Apache-2.0, https://github.com/kopperx/RelayVSR (pobierany przy instalacji)
- RIFE (`rife/`): MIT, kod z https://github.com/Fannovel16/ComfyUI-Frame-Interpolation, model z https://github.com/hzwer/Practical-RIFE
