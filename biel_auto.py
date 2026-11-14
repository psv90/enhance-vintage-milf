"""Automatyczny balans bieli dla kazdego fragmentu filmu.

Co OKNO_S sekund mierzy srednia biel (jasne, prawie szare piksele) i srednia skore.
- Jest biel w kadrze: mnozniki neutralizuja biel z sila SILA_BIELI.
- Nie ma bieli: mnozniki dopasowuja odcien skory do skory z ostatniego fragmentu z biela,
  z sila SILA_SKORY.
- Nie ma ani bieli, ani skory: zostaja poprzednie mnozniki.
Na koniec mnozniki sa wygladzane, zeby przenikania scen nie skakaly kolorem.

Uzycie samodzielne (wypisuje punkty T:R,G,B dla biel_scen.py):
python biel_auto.py WEJSCIE.mp4
"""
import sys

import numpy as np

from ustawienia import JASNOSC, OKNO_S, SILA_BIELI, SILA_SKORY, WYGLADZANIE_OKIEN
from wideo import probe, read_frames

W, H = 480, 360
MIN_UDZIAL = 0.03  # biel/skora musi zajmowac co najmniej 3% kadru
SKORA_DOMYSLNA = (0.72, 0.60)  # G/R i B/R skory, gdy w filmie nie bylo jeszcze bieli
LUMA = np.array([0.299, 0.587, 0.114])


def zmierz(path):
    """Zwraca liste (czas, srednia_biel|None, srednia_skora|None) co OKNO_S sekund."""
    _, _, fps = probe(path)
    na_okno = max(1, round(OKNO_S * fps))
    wynik, biel, skora, n = [], [], [], 0
    for buf in read_frames(path, W, H, scale=True):
        f = np.frombuffer(buf, np.uint8).reshape(-1, 3).astype(np.float32)
        y = f @ LUMA
        rozpietosc = f.max(1) - f.min(1)
        r, g, b = f[:, 0], f[:, 1], f[:, 2]
        m_biel = (y > 140) & (rozpietosc < 40)
        m_skora = (y > 70) & (y < 200) & (r > g) & (g > b) & ((r - b) > 25)
        biel.append(f[m_biel].mean(0) if m_biel.mean() > MIN_UDZIAL else None)
        skora.append(f[m_skora].mean(0) if m_skora.mean() > MIN_UDZIAL else None)
        n += 1
        if n % na_okno == 0:
            wynik.append((n / fps - OKNO_S / 2, _srednia(biel), _srednia(skora)))
            biel, skora = [], []
    if biel:
        wynik.append((n / fps, _srednia(biel), _srednia(skora)))
    return wynik


def _srednia(lista):
    ok = [v for v in lista if v is not None]
    # fragment liczy sie tylko, gdy wartosc byla w wiekszosci klatek okna
    return np.mean(ok, axis=0) if len(ok) * 2 >= len(lista) else None


def _norm(g):
    """Skaluje mnozniki tak, zeby jasnosc wzrosla dokladnie o JASNOSC."""
    return g * JASNOSC / float(g @ LUMA)


def mnozniki(pomiary):
    """Zamienia pomiary na wygladzone mnozniki RGB, po jednym na okno."""
    g = np.ones(3)
    cel_skory = None
    surowe = []
    for _, biel, skora in pomiary:
        if biel is not None:
            pelne = biel.mean() / biel
            g = _norm(1 + SILA_BIELI * (pelne - 1))
            if skora is not None:
                s = skora * g
                cel_skory = (s[1] / s[0], s[2] / s[0])
        elif skora is not None:
            gr, br = cel_skory or SKORA_DOMYSLNA
            pelne = np.array([1.0, gr * skora[0] / skora[1], br * skora[0] / skora[2]])
            g_ref = g if cel_skory else np.ones(3)
            g = _norm(g_ref + SILA_SKORY * (_norm(pelne) - g_ref))
        surowe.append(g.copy())
    surowe = np.array(surowe)
    k = WYGLADZANIE_OKIEN // 2
    pad = np.pad(surowe, ((k, k), (0, 0)), mode="edge")
    return np.array([pad[i:i + 2 * k + 1].mean(0) for i in range(len(surowe))])


def punkty(path):
    """Lista (czas, [R, G, B]) gotowa dla biel_scen.main."""
    pomiary = zmierz(path)
    g = mnozniki(pomiary)
    return [(t, list(map(float, gi))) for (t, _, _), gi in zip(pomiary, g)]


if __name__ == "__main__":
    for t, (r, g, b) in punkty(sys.argv[1]):
        print(f"{t:6.2f}s  R {r:.3f}  G {g:.3f}  B {b:.3f}")
