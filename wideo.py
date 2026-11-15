"""Wspolne: odczyt parametrow i klatek filmu przez ffmpeg."""
import os
import subprocess

from ustawienia import FFMPEG_BIN


def uzyj_ffmpeg_z_silnika():
    """ffmpeg z instalatora (folder silnik) ma pierwszenstwo przed systemowym."""
    if (FFMPEG_BIN / "ffmpeg.exe").exists() and str(FFMPEG_BIN) not in os.environ["PATH"]:
        os.environ["PATH"] = f"{FFMPEG_BIN}{os.pathsep}{os.environ['PATH']}"


def probe(path):
    """Zwraca (szerokosc, wysokosc, kl./s) pierwszego strumienia wideo."""
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate", "-of", "csv=p=0", str(path),
    ], text=True).strip()
    w, h, rate = out.split(",")
    num, den = rate.split("/")
    return int(w), int(h), int(num) / int(den)


def dlugosc(path):
    """Dlugosc filmu w sekundach (0, gdy ffprobe jej nie poda)."""
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path),
    ], text=True).strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def kadr(path, cel, sekunda, szerokosc=960):
    """Zapisuje jedna klatke filmu z podanej sekundy jako JPG o danej szerokosci."""
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-ss", f"{sekunda:.2f}", "-i", str(path), "-frames:v", "1",
        "-vf", f"scale={szerokosc}:-2", "-q:v", "3", str(cel),
    ], check=True)


def read_frames(path, w, h, scale=False):
    """Generator surowych klatek RGB24 (bytes); scale=True zmniejsza je do w x h."""
    size = w * h * 3
    vf = ["-vf", f"scale={w}:{h}:flags=area"] if scale else []
    reader = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", str(path), *vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE,
    )
    try:
        while True:
            buf = reader.stdout.read(size)
            if len(buf) < size:
                break
            yield buf
    finally:
        reader.stdout.close()
        reader.wait()
