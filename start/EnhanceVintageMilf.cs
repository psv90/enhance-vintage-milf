// Enhance Vintage Milf.exe - starter programu.
// Za pierwszym razem uruchamia instaluj.ps1 (silnik w folderze "silnik"), potem otwiera okno
// programu: pythonw aplikacja.py [FILMY...]. Filmy upuszczone na exe trafiaja do kolejki.
// Kompilacja bez instalowania czegokolwiek: zbuduj_exe.ps1 (kompilator C# z .NET Framework w Windows).
using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Windows.Forms;

static class Start
{
    const string Tytul = "Enhance Vintage MILF";

    [STAThread]
    static int Main(string[] args)
    {
        string baza = AppDomain.CurrentDomain.BaseDirectory;
        string znacznik = Path.Combine(baza, @"silnik\zainstalowane.txt");
        string pythonw = Path.Combine(baza, @"silnik\RelayVSR\.venv\Scripts\pythonw.exe");
        string aplikacja = Path.Combine(baza, "aplikacja.py");

        if (!File.Exists(znacznik) && !Instaluj(baza))
            return 1;

        if (!File.Exists(pythonw) || !File.Exists(aplikacja))
        {
            Blad("Brakuje plików programu (" + (File.Exists(pythonw) ? "aplikacja.py" : @"silnik\...\pythonw.exe") +
                 ").\n\nUsuń plik silnik\\zainstalowane.txt i uruchom program ponownie - instalator dokończy brakujące części.");
            return 1;
        }

        var start = new ProcessStartInfo(pythonw)
        {
            Arguments = Cudzyslow(aplikacja) + string.Concat(args.Select(a => " " + Cudzyslow(a))),
            WorkingDirectory = baza,
            UseShellExecute = false,
        };
        try { Process.Start(start); }
        catch (Exception e) { Blad("Nie udało się uruchomić programu:\n" + e.Message); return 1; }
        return 0;
    }

    static bool Instaluj(string baza)
    {
        var odp = MessageBox.Show(
            "Pierwsze uruchomienie: program pobierze potrzebne części (Python, PyTorch, RelayVSR, modele, ffmpeg) " +
            "do folderu \"silnik\" obok programu.\n\nPotrzeba ok. 20 GB miejsca i internetu. Trwa to od kilkunastu minut " +
            "do godziny. Jeśli się przerwie, uruchom program ponownie - dokończy.\n\nZacząć?",
            Tytul, MessageBoxButtons.OKCancel, MessageBoxIcon.Information);
        if (odp != DialogResult.OK)
            return false;

        var ps = new ProcessStartInfo("powershell.exe",
            "-NoProfile -ExecutionPolicy Bypass -File " + Cudzyslow(Path.Combine(baza, "instaluj.ps1")))
        {
            WorkingDirectory = baza,
            UseShellExecute = false,
        };
        try
        {
            using (var p = Process.Start(ps))
            {
                p.WaitForExit();
                if (p.ExitCode == 0)
                    return true;
            }
        }
        catch (Exception e) { Blad("Nie udało się uruchomić instalatora:\n" + e.Message); return false; }
        Blad("Instalacja nie skończyła się. Uruchom program ponownie - instalator dokończy od miejsca, w którym przerwał.");
        return false;
    }

    static string Cudzyslow(string s)
    {
        return "\"" + s.Replace("\"", "\\\"") + "\"";
    }

    static void Blad(string tekst)
    {
        MessageBox.Show(tekst, Tytul, MessageBoxButtons.OK, MessageBoxIcon.Error);
    }
}
