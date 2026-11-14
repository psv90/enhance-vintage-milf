"""Okienka przy starcie: wybor filmu i liczby klatek na sekunde (tylko myszka)."""
import ctypes
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

TLO, KARTA, TEKST, AKCENT = "#14191f", "#1f2a35", "#f2f5f8", "#3aa8e6"
FILMY = [("Wideo", "*.mp4 *.mkv *.mov *.avi *.webm *.m4v"), ("Wszystkie pliki", "*.*")]
IKONA = Path(__file__).with_name("ikona.ico")

try:  # ostre litery przy skalowaniu ekranu
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except (AttributeError, OSError):
    pass


def _okno(tytul):
    root = tk.Tk()
    root.title(tytul)
    if IKONA.exists():
        root.iconbitmap(str(IKONA))
    root.configure(bg=TLO)
    root.resizable(False, False)
    root.attributes("-topmost", True)
    return root


def wybierz_plik():
    """Zwraca sciezke wybranego filmu albo None."""
    root = _okno("Poprawa wideo")
    root.withdraw()
    sciezka = filedialog.askopenfilename(parent=root, title="Wybierz film do poprawy", filetypes=FILMY)
    root.destroy()
    return sciezka or None


def wybierz_kl_s(nazwa_filmu, opcje):
    """Duze przyciski z liczba klatek; zwraca wybrana liczbe albo None (zamkniete okno)."""
    root = _okno("Płynność")
    wynik = {"kl_s": None}
    tk.Label(root, text=nazwa_filmu, bg=TLO, fg=TEKST, font=("Segoe UI", 11)).pack(padx=24, pady=(20, 4))
    tk.Label(root, text="Ile klatek na sekundę?", bg=TLO, fg=TEKST,
             font=("Georgia", 18, "bold")).pack(padx=24, pady=(0, 16))
    rzad = tk.Frame(root, bg=TLO)
    rzad.pack(padx=24, pady=(0, 24))

    for kl_s in opcje:
        def wybierz(k=kl_s):
            wynik["kl_s"] = k
            root.destroy()

        b = tk.Button(rzad, text=f"{kl_s}\nkl./s", command=wybierz, width=8, height=3,
                      font=("Segoe UI", 16, "bold"), bg=KARTA, fg=TEKST, bd=0, cursor="hand2",
                      activebackground=AKCENT, activeforeground=TLO)
        b.bind("<Enter>", lambda e, b=b: b.configure(bg=AKCENT, fg=TLO))
        b.bind("<Leave>", lambda e, b=b: b.configure(bg=KARTA, fg=TEKST))
        b.pack(side="left", padx=8)

    root.bind("<Escape>", lambda e: root.destroy())
    root.update_idletasks()
    x = (root.winfo_screenwidth() - root.winfo_width()) // 2
    y = (root.winfo_screenheight() - root.winfo_height()) // 2
    root.geometry(f"+{x}+{y}")
    root.mainloop()
    return wynik["kl_s"]
