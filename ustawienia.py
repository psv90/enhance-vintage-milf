"""Wszystkie sciezki i parametry poprawy wideo w jednym miejscu.

Wszystko, co instaluje instaluj.ps1, lezy w folderze `silnik` obok skryptow,
wiec caly folder mozna przeniesc na inny komputer.
"""
from pathlib import Path

BAZA = Path(__file__).resolve().parent
SILNIK = BAZA / "silnik"

# RelayVSR (powiekszanie 4x)
RELAYVSR_DIR = SILNIK / "RelayVSR"
RELAYVSR_PY = RELAYVSR_DIR / ".venv" / "Scripts" / "python.exe"
RELAYVSR_WINDOW = 16  # klatka wzorcowa co 15 klatek; 8 dalo tylko +2,5% ostrosci przy 14x dluzszym czasie

# RIFE (interpolacja klatek) - kod i wagi sa w paczce (licencja MIT, rife/LICENSE)
RIFE_DIR = BAZA / "rife"
RIFE_ARCH = RIFE_DIR / "rife_arch.py"
RIFE_CKPT = RIFE_DIR / "rife49.pth"
RIFE_ARCH_VER = "4.7"  # rife49 uzywa architektury 4.7
KL_S_DO_WYBORU = (60, 120)  # przyciski w okienku przy starcie
# mnoznik klatek = wybrane kl./s / kl./s filmu, zaokraglony (np. 30 -> 120 to x4, 25 -> 120 to x5 = 125)

# Balans bieli (biel_auto.py)
SILA_BIELI = 0.9  # jak mocno neutralizowac biel sciany (1 = calkiem szara)
SILA_SKORY = 0.5  # gdy w kadrze nie ma bieli: jak mocno dopasowac skore do poprzedniej sceny
JASNOSC = 1.027  # mnoznik jasnosci po balansie (jak w recznie dobranej korekcji)
OKNO_S = 0.5  # co ile sekund mierzyc kolory
WYGLADZANIE_OKIEN = 5  # srednia z tylu okien, zeby przejscia scen byly plynne

# Kontrast, odszumianie, wyostrzanie (po balansie bieli)
FILTRY = (
    "curves=all='0/0 0.12/0.09 0.5/0.52 0.8/0.9 1/1',eq=saturation=0.97,"
    "hqdn3d=2:1.5:5:4,cas=0.4"
)

# Film porownawczy przed/po
POROWNANIE_MAKS_WYS = 1080  # kazda polowa najwyzej tyle pikseli wysokosci
CZCIONKA = "C\\:/Windows/Fonts/arialbd.ttf"  # sciezka w skladni filtra drawtext

# ffmpeg z instalatora (uzywany, gdy w systemie nie ma wlasnego)
FFMPEG_BIN = SILNIK / "ffmpeg" / "bin"

# Pliki robocze (usuwane po udanym przebiegu) i cache kompilatorow GPU
ROBOCZY_DIR = SILNIK / "_robocze"
CACHE_ENV = {
    "TRITON_CACHE_DIR": str(SILNIK / "_cache" / "triton"),
    "TORCHINDUCTOR_CACHE_DIR": str(SILNIK / "_cache" / "inductor"),
}
