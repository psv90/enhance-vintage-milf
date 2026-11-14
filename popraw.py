"""Pelna poprawa filmu jednym poleceniem.

1. RelayVSR: powiekszenie 4x (dzwiek doklejany z oryginalu)
2. Balans bieli osobno dla kazdego fragmentu + kontrast, odszumianie, wyostrzanie
3. RIFE: wiecej klatek na sekunde (60 albo 120, wybor w okienku)
4. Film porownawczy przed/po

Uzycie: python popraw.py [FILM.mp4] [--kl-s 60|120]
Bez filmu otwiera okno wyboru pliku, bez --kl-s pyta o liczbe klatek.
Wynik obok oryginalu: FILM_poprawiony_120fps.mp4 i FILM_porownanie_120fps.mp4
"""
import argparse
import os
import shutil
import subprocess
import time
from pathlib import Path

import biel_auto
import biel_scen
import okno
import porownanie
import rife
from ustawienia import (CACHE_ENV, FFMPEG_BIN, FILTRY, KL_S_DO_WYBORU, RELAYVSR_DIR, RELAYVSR_PY,
                        RELAYVSR_WINDOW, ROBOCZY_DIR)
from wideo import probe

if (FFMPEG_BIN / "ffmpeg.exe").exists():  # ffmpeg z instalatora ma pierwszenstwo
    os.environ["PATH"] = f"{FFMPEG_BIN}{os.pathsep}{os.environ['PATH']}"

KROKI = 4


def krok(nr, opis):
    print(f"\n[{nr}/{KROKI}] {opis}", flush=True)
    return time.perf_counter()


def koniec(start):
    print(f"      gotowe w {(time.perf_counter() - start) / 60:.1f} min", flush=True)


def wolna_nazwa(path):
    """Nie nadpisuje istniejacego pliku: dokleja _2, _3..."""
    if not path.exists():
        return path
    i = 2
    while (p := path.with_name(f"{path.stem}_{i}{path.suffix}")).exists():
        i += 1
    return p


def powieksz(src, roboczy):
    bez_dzwieku = roboczy / "1_x4_bez_dzwieku.mp4"
    x4 = roboczy / "1_x4.mp4"
    subprocess.run(
        [str(RELAYVSR_PY), "inference.py", "--input", str(src), "--output", str(bez_dzwieku),
         "--window-size", str(RELAYVSR_WINDOW), "--overwrite"],
        cwd=RELAYVSR_DIR, env={**os.environ, **CACHE_ENV}, check=True,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(bez_dzwieku), "-i", str(src),
         "-map", "0:v", "-map", "1:a?", "-c", "copy", "-shortest", str(x4)],
        check=True,
    )
    return x4


def main(src, kl_s):
    src = Path(src).resolve()
    w, h, fps = probe(src)
    mnoznik = max(1, round(kl_s / fps))
    wynik_fps = f"{fps * mnoznik:g}"
    cel = wolna_nazwa(src.with_name(f"{src.stem}_poprawiony_{wynik_fps}fps.mp4"))
    cel_por = wolna_nazwa(src.with_name(f"{src.stem}_porownanie_{wynik_fps}fps.mp4"))
    roboczy = ROBOCZY_DIR / src.stem
    roboczy.mkdir(parents=True, exist_ok=True)
    print(f"Film: {src.name}  {w}x{h}, {fps:g} kl./s -> {wynik_fps} kl./s (x{mnoznik})")
    print(f"Wynik: {cel}")
    caly = time.perf_counter()

    t = krok(1, f"Powiekszanie 4x przez RelayVSR do {w * 4}x{h * 4}")
    x4 = powieksz(src, roboczy)
    koniec(t)

    t = krok(2, "Balans bieli dla kazdego fragmentu, kontrast, odszumianie, wyostrzanie")
    kolor = roboczy / "2_kolor.mp4"
    biel_scen.main(x4, kolor, FILTRY, biel_auto.punkty(x4))
    koniec(t)

    t = krok(3, f"Interpolacja RIFE do {wynik_fps} kl./s")
    if mnoznik > 1:
        rife.main(kolor, cel, mnoznik)
    else:
        shutil.copyfile(kolor, cel)
    koniec(t)

    t = krok(4, "Film porownawczy przed/po")
    porownanie.zrob(src, cel, cel_por)
    koniec(t)

    shutil.rmtree(roboczy, ignore_errors=True)
    print(f"\nGOTOWE w {(time.perf_counter() - caly) / 60:.1f} min")
    print(f"  poprawiony:  {cel}")
    print(f"  porownanie:  {cel_por}")
    subprocess.run(["explorer", f"/select,{cel}"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Pelna poprawa filmu")
    ap.add_argument("film", nargs="?")
    ap.add_argument("--kl-s", type=int, choices=KL_S_DO_WYBORU)
    a = ap.parse_args()
    film = a.film or okno.wybierz_plik()
    if not film:
        raise SystemExit("Nie wybrano filmu.")
    kl_s = a.kl_s or okno.wybierz_kl_s(Path(film).name, KL_S_DO_WYBORU)
    if not kl_s:
        raise SystemExit("Nie wybrano liczby klatek.")
    main(film, kl_s)
