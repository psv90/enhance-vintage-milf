"""Wspolne: odczyt parametrow i klatek filmu przez ffmpeg."""
import subprocess


def probe(path):
    """Zwraca (szerokosc, wysokosc, kl./s) pierwszego strumienia wideo."""
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate", "-of", "csv=p=0", str(path),
    ], text=True).strip()
    w, h, rate = out.split(",")
    num, den = rate.split("/")
    return int(w), int(h), int(num) / int(den)


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
