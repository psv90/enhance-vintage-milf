"""Film porownawczy: oryginal i wynik obok siebie, z podpisami PRZED i PO.

Uzycie: python porownanie.py PRZED.mp4 PO.mp4 WYJSCIE.mp4
Oryginal jest rozciagany do rozmiaru wyniku i dostaje te sama liczbe kl./s.
Dzwiek z filmu PO.
"""
import subprocess
import sys
from pathlib import Path

from ustawienia import CZCIONKA, POROWNANIE_MAKS_WYS
from wideo import probe


def zrob(przed, po, cel):
    w, h, fps = probe(po)
    wys = min(h, POROWNANIE_MAKS_WYS)
    szer = round(w * wys / h / 2) * 2
    rozm = max(24, wys // 26)
    napis = (f"fontfile='{CZCIONKA}':fontsize={rozm}:fontcolor=white:box=1:boxcolor=black@0.55:"
             f"boxborderw={rozm // 3}:x={rozm // 2}:y={rozm // 2}")
    graf = (
        f"[0:v]fps={fps:g},scale={szer}:{wys}:flags=lanczos,setsar=1,drawtext=text='PRZED':{napis}[a];"
        f"[1:v]scale={szer}:{wys}:flags=lanczos,setsar=1,drawtext=text='PO':{napis}[b];"
        f"[a][b]hstack=shortest=1[v]"
    )
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(przed), "-i", str(po),
        "-filter_complex", graf, "-map", "[v]", "-map", "1:a?",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-c:a", "copy", str(cel),
    ], check=True)


if __name__ == "__main__":
    zrob(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
