"""Balans bieli osobno dla scen + dalsze filtry ffmpeg.

Uzycie: python biel_scen.py WEJSCIE.mp4 WYJSCIE.mp4 "FILTRY_FFMPEG" T:R,G,B [T:R,G,B ...]
Kazde T:R,G,B to mnozniki kanalow od chwili T (sekundy). Miedzy kolejnymi
punktami mnozniki zmieniaja sie liniowo (np. przy przenikaniu scen), po ostatnim
zostaja stale. Dzwiek kopiowany z wejscia.
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

from wideo import probe, read_frames

DEVICE = torch.device("cuda")


def parse_keys(args):
    keys = []
    for a in args:
        t, rgb = a.split(":")
        keys.append((float(t), [float(v) for v in rgb.split(",")]))
    return sorted(keys)


def gains_at(keys, t):
    times = [k[0] for k in keys]
    return [float(np.interp(t, times, [k[1][c] for k in keys])) for c in range(3)]


@torch.no_grad()
def main(src, dst, filters, keys):
    w, h, fps = probe(src)
    writer = subprocess.Popen([
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", f"{fps:g}", "-i", "-",
        "-i", str(src), "-map", "0:v", "-map", "1:a?", "-vf", filters,
        "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-shortest", str(dst),
    ], stdin=subprocess.PIPE)
    n = 0
    for buf in read_frames(src, w, h):
        g = torch.tensor(gains_at(keys, n / fps), device=DEVICE).view(1, 1, 3)
        frame = torch.frombuffer(bytearray(buf), dtype=torch.uint8).to(DEVICE).view(h, w, 3)
        out = (frame.float() * g).round_().clamp_(0, 255).byte()
        writer.stdin.write(out.cpu().numpy().tobytes())
        n += 1
    writer.stdin.close()
    writer.wait()
    print(f"Gotowe: {n} klatek -> {dst}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], parse_keys(sys.argv[4:]))
