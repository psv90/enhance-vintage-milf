"""Mnozy liczbe klatek filmu siecia RIFE 4.9 (z wezlow comfyui-frame-interpolation).

Uzycie: python rife.py WEJSCIE.mp4 WYJSCIE.mp4 [MNOZNIK]
MNOZNIK 2 = 30 -> 60 kl./s, 4 = 30 -> 120 kl./s (domyslnie 2).
Dzwiek kopiowany z wejscia. Wymaga torch z CUDA i ffmpeg w PATH.
"""
import importlib.util
import subprocess
import sys
import types
from pathlib import Path

import torch

from ustawienia import RIFE_ARCH as ARCH, RIFE_ARCH_VER as ARCH_VER, RIFE_CKPT as CKPT
from wideo import probe, read_frames

SCALE_LIST = [8, 4, 2, 1]
DEVICE = torch.device("cuda")


def load_model():
    # rife_arch importuje comfy.model_management tylko po get_torch_device
    comfy = types.ModuleType("comfy")
    mm = types.ModuleType("comfy.model_management")
    mm.get_torch_device = lambda: DEVICE
    comfy.model_management = mm
    sys.modules.setdefault("comfy", comfy)
    sys.modules.setdefault("comfy.model_management", mm)
    spec = importlib.util.spec_from_file_location("rife_arch", ARCH)
    arch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arch)
    model = arch.IFNet(arch_ver=ARCH_VER)
    model.load_state_dict(torch.load(CKPT, map_location="cpu"))
    return model.eval().to(DEVICE)


def to_tensor(buf, w, h):
    t = torch.frombuffer(bytearray(buf), dtype=torch.uint8).to(DEVICE).view(h, w, 3)
    return t.permute(2, 0, 1)[None].float() / 255


def to_bytes(t, h, w):
    t = t[0, :, :h, :w].clamp(0, 1).mul(255).round().byte().permute(1, 2, 0)
    return t.contiguous().cpu().numpy().tobytes()


@torch.no_grad()
def main(src, dst, mult):
    w, h, fps = probe(src)
    writer = subprocess.Popen([
        "ffmpeg", "-y", "-v", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", f"{fps * mult:g}", "-i", "-",
        "-i", str(src), "-map", "0:v", "-map", "1:a?",
        "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-shortest", str(dst),
    ], stdin=subprocess.PIPE)
    model = load_model()
    frames = read_frames(src, w, h)
    prev_buf = next(frames)
    prev = to_tensor(prev_buf, w, h)
    n = 0
    for buf in frames:
        cur = to_tensor(buf, w, h)
        writer.stdin.write(prev_buf)
        for k in range(1, mult):
            mid = model(prev, cur, k / mult, SCALE_LIST, training=False, fastmode=True, ensemble=False)
            writer.stdin.write(to_bytes(mid, h, w))
        prev, prev_buf = cur, buf
        n += 1
        if n % 100 == 0:
            print(f"{n} par klatek", flush=True)
    # ostatnia klatka powtorzona, zeby czas filmu sie zgadzal
    for _ in range(mult):
        writer.stdin.write(prev_buf)
    writer.stdin.close()
    writer.wait()
    print(f"Gotowe: {mult * (n + 1)} klatek, {fps * mult:g} kl./s -> {dst}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 2)
