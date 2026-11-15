"""Enhance Vintage Milf - aplikacja okienkowa.

Maly serwer HTTP (tylko biblioteka standardowa) serwuje ekran z folderu ui/ i API.
Poprawe robi popraw.py uruchamiany w tle; serwer czyta jego wyjscie i liczy postep.
Okno to Edge w trybie aplikacji (--app), a gdy Edge nie ma - domyslna przegladarka.

Uzycie: pythonw aplikacja.py [FILM ...]   (film mozna tez upuscic na skrot)
Drugie uruchomienie nie otwiera drugiej kopii: dorzuca filmy do kolejki i pokazuje okno.
"""
import hashlib
import json
import math
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ustawienia import (BAZA, CZAS_WZORZEC, EDGE, HISTORIA, KADRY_DIR, KL_S_DO_WYBORU, RELAYVSR_PY,
                        SILA_BIELI, SILNIK, UDZIAL_KROKOW, UI_DIR)
import wideo

BEZ_OKNA = subprocess.CREATE_NO_WINDOW
PLIK_PORTU = SILNIK / "aplikacja.json"
DZIENNIK = SILNIK / "aplikacja.log"
COMFYUI_PORT = 8188
CISZA_DO_ZAMKNIECIA = 25  # s bez zapytan z okna (okno zamkniete) -> koniec, gdy nic sie nie liczy

if sys.stderr is None:  # pythonw nie ma konsoli: bledy do dziennika
    SILNIK.mkdir(exist_ok=True)
    sys.stderr = sys.stdout = open(DZIENNIK, "a", encoding="utf-8", buffering=1)
wideo.uzyj_ffmpeg_z_silnika()


class Stan:
    """Caly stan aplikacji; dostep tylko przez blokade."""

    def __init__(self):
        self.lock = threading.RLock()
        self.stan = "pusty"  # pusty | plik | trwa | gotowe | blad
        self.plik = None
        self.kolejka = []
        self.kl_s = max(KL_S_DO_WYBORU)
        self.sila = SILA_BIELI
        self.porownanie = True
        self.otworz_folder = False
        self.krok = 0
        self.krok_start = 0.0
        self.start = 0.0
        self.koniec = 0.0
        self.log = []
        self.wynik = None
        self.wynik_por = None
        self.blad = None
        self.proces = None
        self.anulowano = False
        self.historia = _wczytaj_historie()
        self.gpu = {"nazwa": "", "uzyte": 0, "razem": 0, "comfyui": False}
        self.ostatni_ping = time.time()


def _wczytaj_historie():
    try:
        return json.loads(HISTORIA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


S = Stan()


# ---------- pliki ----------

def info_pliku(sciezka):
    p = Path(sciezka)
    w, h, fps = wideo.probe(p)
    return {"sciezka": str(p), "nazwa": p.name, "w": w, "h": h, "fps": round(fps, 3),
            "dlugosc": round(wideo.dlugosc(p), 1), "rozmiar": p.stat().st_size}


def szacunek(plik, kl_s):
    """Szacowany czas calej poprawy w sekundach, przeskalowany z wzorca z README."""
    ile = plik["dlugosc"] * plik["fps"] * plik["w"] * plik["h"]
    s = CZAS_WZORZEC[1] * ile / CZAS_WZORZEC[0]
    return max(30.0, s * (0.8 + 0.2 * kl_s / max(KL_S_DO_WYBORU)))


def dodaj_pliki(sciezki):
    """Pierwszy film zostaje wybrany (gdy nic nie trwa i nic nie wybrano), reszta idzie do kolejki."""
    bledy = []
    with S.lock:
        for s in sciezki:
            try:
                i = info_pliku(s)
            except Exception as e:  # nie film albo uszkodzony
                bledy.append(f"{Path(s).name}: {e}")
                continue
            if S.plik is None and S.stan in ("pusty", "gotowe", "blad"):
                S.plik, S.stan, S.blad = i, "plik", None
            else:
                S.kolejka.append(i)
    return bledy


def wybierz_z_dysku():
    """Okno wyboru plikow z okno.py w osobnym procesie (tkinter nie lubi watkow serwera)."""
    kod = "import json, okno; print(json.dumps(okno.wybierz_plik(wiele=True)))"
    out = subprocess.run([str(RELAYVSR_PY), "-c", kod], cwd=BAZA, capture_output=True, text=True,
                         encoding="utf-8", creationflags=BEZ_OKNA).stdout.strip()
    try:
        return json.loads(out.splitlines()[-1]) if out else []
    except ValueError:
        return []


# ---------- poprawa ----------

def start():
    with S.lock:
        if S.stan == "trwa" or S.plik is None:
            return False
        S.stan, S.krok, S.log, S.blad, S.wynik, S.wynik_por, S.anulowano = "trwa", 0, [], None, None, None, False
        S.start = S.krok_start = time.time()
        plik, kl_s, sila, porownaj = S.plik, S.kl_s, S.sila, S.porownanie
    cmd = [str(RELAYVSR_PY), "popraw.py", plik["sciezka"], "--kl-s", str(kl_s), "--bez-folderu"]
    if not porownaj:
        cmd.append("--bez-porownania")
    env = {**os.environ, "EVM_SILA_BIELI": f"{sila:.2f}", "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.Popen(cmd, cwd=BAZA, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace", creationflags=BEZ_OKNA)
    with S.lock:
        S.proces = proc
    threading.Thread(target=_czytaj, args=(proc,), daemon=True).start()
    return True


def _czytaj(proc):
    for linia in proc.stdout:
        linia = linia.rstrip()
        if not linia:
            continue
        with S.lock:
            S.log = (S.log + [linia])[-300:]
            if m := re.match(r"\[(\d)/4\]", linia.strip()):
                S.krok, S.krok_start = int(m.group(1)), time.time()
            elif "poprawiony:" in linia:
                S.wynik = linia.split("poprawiony:", 1)[1].strip()
            elif "porownanie:" in linia:
                S.wynik_por = linia.split("porownanie:", 1)[1].strip()
    kod = proc.wait()
    with S.lock:
        S.proces, S.koniec = None, time.time()
        if S.anulowano:
            S.stan, S.krok = "plik", 0
            return
        if kod == 0 and S.wynik:
            S.stan = "gotowe"
            S.historia = ([{"nazwa": Path(S.wynik).name, "sciezka": S.wynik, "zrodlo": S.plik["nazwa"],
                            "data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "minuty": round((S.koniec - S.start) / 60, 1)}] + S.historia)[:30]
            try:
                HISTORIA.write_text(json.dumps(S.historia, ensure_ascii=False, indent=1), encoding="utf-8")
            except OSError:
                pass
            if S.otworz_folder:
                subprocess.Popen(["explorer", f"/select,{S.wynik}"])
            if S.kolejka:  # nastepny film z kolejki po chwili, zeby bylo widac "Gotowe"
                threading.Timer(4, _nastepny).start()
        else:
            S.stan = "blad"
            S.blad = _opis_bledu(S.log)


def _nastepny():
    with S.lock:
        if S.stan != "gotowe" or not S.kolejka:
            return
        S.plik, S.stan = S.kolejka.pop(0), "plik"
    start()


def _opis_bledu(log):
    tekst = "\n".join(log[-40:])
    if "out of memory" in tekst.lower():
        return "Karcie graficznej zabrakło pamięci. Zamknij ComfyUI, gry i inne programy używające karty, a potem spróbuj jeszcze raz."
    if "No such file" in tekst or "FileNotFoundError" in tekst:
        return "Nie znalazłem pliku albo programu potrzebnego do poprawy. Sprawdź, czy film nadal jest na dysku."
    return "Poprawa przerwała się z błędem. Szczegóły są w logu poniżej."


def anuluj():
    with S.lock:
        proc = S.proces
        if not proc:
            return False
        S.anulowano = True
    subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, creationflags=BEZ_OKNA)
    return True


def postep():
    """Procent calosci: ukonczone kroki + szacowana czesc biezacego (najwyzej 95% kroku)."""
    if S.stan == "gotowe":
        return 100.0, S.koniec - S.start, 0.0
    if S.stan != "trwa" or not S.plik:
        return 0.0, 0.0, szacunek(S.plik, S.kl_s) if S.plik else 0.0
    teraz = time.time()
    szac = szacunek(S.plik, S.kl_s)
    k = max(1, S.krok)
    udzial = UDZIAL_KROKOW[k - 1]
    # krzywa nasycenia: przy szacowanym czasie kroku ok. 70%, potem coraz wolniej, nigdy 100% przed koncem kroku
    czesc = min(0.97, 1 - math.exp(-1.2 * (teraz - S.krok_start) / max(1.0, szac * udzial))) if S.krok else 0.0
    proc = (sum(UDZIAL_KROKOW[:k - 1]) + udzial * czesc) * 100
    minelo = teraz - S.start
    zostalo = minelo * (100 - proc) / proc if proc > 5 else max(0.0, szac - minelo)
    return proc, minelo, zostalo


# ---------- karta graficzna ----------

def _sledz_gpu():
    while True:
        gpu = dict(S.gpu)
        try:
            out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.used,memory.total",
                                  "--format=csv,noheader,nounits"], capture_output=True, text=True,
                                 creationflags=BEZ_OKNA, timeout=5).stdout.strip().splitlines()[0]
            nazwa, uzyte, razem = [x.strip() for x in out.split(",")]
            gpu.update(nazwa=nazwa.replace("NVIDIA GeForce ", ""), uzyte=int(uzyte), razem=int(razem))
        except Exception:
            pass
        with socket.socket() as s:
            s.settimeout(0.3)
            gpu["comfyui"] = s.connect_ex(("127.0.0.1", COMFYUI_PORT)) == 0
        with S.lock:
            S.gpu = gpu
        time.sleep(3)


# ---------- podglad klatek ----------

def sciezka_kadru(co):
    with S.lock:
        film = S.plik["sciezka"] if co == "src" and S.plik else S.wynik if co == "wynik" else None
        dl = S.plik["dlugosc"] if S.plik else 0
    if not film or not Path(film).exists():
        return None
    st = Path(film).stat()
    klucz = hashlib.md5(f"{film}|{st.st_mtime}|{st.st_size}".encode()).hexdigest()[:16]
    cel = KADRY_DIR / f"{klucz}.jpg"
    if not cel.exists():
        KADRY_DIR.mkdir(parents=True, exist_ok=True)
        wideo.kadr(film, cel, dl / 3 if dl else 1)
    return cel


# ---------- HTTP ----------

def stan_json():
    with S.lock:
        proc, minelo, zostalo = postep()
        return {
            "stan": S.stan, "plik": S.plik, "kolejka": S.kolejka, "historia": S.historia[:8],
            "kl_s": S.kl_s, "kl_s_opcje": list(KL_S_DO_WYBORU), "sila": S.sila, "porownanie": S.porownanie,
            "otworz_folder": S.otworz_folder, "krok": S.krok, "postep": round(proc, 1),
            "minelo": round(minelo), "zostalo": round(zostalo),
            "szacunek": round(szacunek(S.plik, S.kl_s)) if S.plik else 0,
            "log": S.log[-60:], "wynik": S.wynik, "wynik_por": S.wynik_por, "blad": S.blad, "gpu": S.gpu,
        }


def akcja(nazwa, dane):
    if nazwa == "wybierz":
        return {"bledy": dodaj_pliki(wybierz_z_dysku())}
    if nazwa == "dodaj":
        return {"bledy": dodaj_pliki(dane.get("sciezki", []))}
    if nazwa == "ustaw":
        with S.lock:
            if dane.get("kl_s") in KL_S_DO_WYBORU:
                S.kl_s = dane["kl_s"]
            if "sila" in dane:
                S.sila = min(1.0, max(0.0, float(dane["sila"])))
            for k in ("porownanie", "otworz_folder"):
                if k in dane:
                    setattr(S, k, bool(dane[k]))
        return {}
    if nazwa == "start":
        return {"ok": start()}
    if nazwa == "anuluj":
        return {"ok": anuluj()}
    if nazwa == "zmien":
        with S.lock:
            if S.stan != "trwa":  # nastepny film z kolejki, a gdy jej nie ma - pusty ekran
                S.plik = S.kolejka.pop(0) if S.kolejka else None
                S.stan = "plik" if S.plik else "pusty"
                S.wynik, S.wynik_por, S.blad = None, None, None
        return {}
    if nazwa == "kolejka":
        with S.lock:
            i, k = int(dane.get("i", -1)), S.kolejka
            if 0 <= i < len(k):
                if dane.get("co") == "usun":
                    k.pop(i)
                elif dane.get("co") == "gora" and i > 0:
                    k[i - 1], k[i] = k[i], k[i - 1]
                elif dane.get("co") == "dol" and i < len(k) - 1:
                    k[i + 1], k[i] = k[i], k[i + 1]
        return {}
    if nazwa == "folder":
        sciezka = dane.get("sciezka") or S.wynik
        if sciezka and Path(sciezka).exists():
            subprocess.Popen(["explorer", f"/select,{sciezka}"])
            return {"ok": True}
        return {"ok": False}
    return None


class Obsluga(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(UI_DIR), **k)

    def log_message(self, *a):  # bez konsoli
        pass

    def _json(self, obj, kod=200):
        dane = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(kod)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(dane)))
        self.end_headers()
        self.wfile.write(dane)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/stan":
            S.ostatni_ping = time.time()
            return self._json(stan_json())
        if u.path == "/api/kadr":
            try:
                cel = sciezka_kadru(parse_qs(u.query).get("co", ["src"])[0])
            except Exception:
                cel = None
            if not cel:
                return self.send_error(404)
            dane = cel.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(dane)))
            self.end_headers()
            return self.wfile.write(dane)
        return super().do_GET()

    def do_POST(self):
        u = urlparse(self.path)
        if not u.path.startswith("/api/") or self.headers.get("Origin", "").split("//")[-1] not in ("", self.headers.get("Host")):
            return self.send_error(403)
        try:
            dl = int(self.headers.get("Content-Length") or 0)
            dane = json.loads(self.rfile.read(dl) or b"{}")
            wynik = akcja(u.path[5:], dane)
        except Exception as e:
            return self._json({"blad": str(e)}, 500)
        return self._json(wynik) if wynik is not None else self.send_error(404)


# ---------- okno i start ----------

def otworz_okno(url):
    if os.environ.get("EVM_BEZ_OKNA"):  # testy: sam serwer
        return
    edge = next((e for e in EDGE if e.exists()), None)
    if edge:
        subprocess.Popen([str(edge), f"--app={url}", "--window-size=1440,960"], creationflags=BEZ_OKNA)
    else:
        webbrowser.open(url)


def juz_dziala():
    """URL dzialajacej kopii programu albo None."""
    try:
        port = json.loads(PLIK_PORTU.read_text(encoding="utf-8"))["port"]
        url = f"http://127.0.0.1:{port}/"
        urllib.request.urlopen(url + "api/stan", timeout=1).read()
        return url
    except Exception:
        return None


def _straznik():
    """Zamyka program, gdy okno jest zamkniete i nic sie nie liczy."""
    while True:
        time.sleep(5)
        with S.lock:
            cicho = time.time() - S.ostatni_ping > CISZA_DO_ZAMKNIECIA
            if cicho and S.stan != "trwa":
                PLIK_PORTU.unlink(missing_ok=True)
                os._exit(0)


def main():
    filmy = [a for a in sys.argv[1:] if Path(a).is_file()]
    if url := juz_dziala():
        if filmy:
            req = urllib.request.Request(url + "api/dodaj", json.dumps({"sciezki": filmy}).encode(),
                                         {"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10).read()
        otworz_okno(url)
        return
    dodaj_pliki(filmy)
    serwer = ThreadingHTTPServer(("127.0.0.1", 0), Obsluga)
    port = serwer.server_address[1]
    SILNIK.mkdir(exist_ok=True)
    PLIK_PORTU.write_text(json.dumps({"port": port}), encoding="utf-8")
    threading.Thread(target=_sledz_gpu, daemon=True).start()
    if not os.environ.get("EVM_BEZ_OKNA"):  # w testach bez okna serwer nie zamyka sie sam
        threading.Thread(target=_straznik, daemon=True).start()
    otworz_okno(f"http://127.0.0.1:{port}/")
    serwer.serve_forever()


if __name__ == "__main__":
    main()
