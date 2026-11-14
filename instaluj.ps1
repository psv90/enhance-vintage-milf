# Instalator Poprawy wideo. Wszystko trafia do folderu "silnik" obok skryptów.
# Można go przerwać i uruchomić ponownie - pominie to, co już jest.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$Baza = $PSScriptRoot
$S = Join-Path $Baza 'silnik'
$Pobrane = Join-Path $S '_pobrane'
$R = Join-Path $S 'RelayVSR'
$Py = Join-Path $R '.venv\Scripts\python.exe'
$Znacznik = Join-Path $S 'zainstalowane.txt'

# Wersje sprawdzone 2026-11-14
$UvUrl = 'https://github.com/astral-sh/uv/releases/download/0.12.18/uv-x86_64-pc-windows-msvc.zip'
$RelayCommit = 'e856773350f53036d825404c9ea9228e6dffadca'
$RelayUrl = "https://github.com/kopperx/RelayVSR/archive/$RelayCommit.zip"
$FfmpegUrl = 'https://github.com/GyanD/codexffmpeg/releases/download/8.1.1/ffmpeg-8.1.1-essentials_build.zip'
$TorchIndex = 'https://download.pytorch.org/whl/cu128'

New-Item -ItemType Directory -Force $S, $Pobrane | Out-Null
$env:UV_CACHE_DIR = Join-Path $S '_cache\uv'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $S 'python'
$env:HF_HOME = Join-Path $S '_cache\hf'

function Krok($nr, $opis) { Write-Host "`n[$nr/6] $opis" -ForegroundColor Cyan }
function Sprawdz($co) { if ($LASTEXITCODE -ne 0) { throw "$co zakończone błędem (kod $LASTEXITCODE)" } }
function Pobierz($url, $plik) {
    if (Test-Path $plik) { return }
    Write-Host "  pobieram $url"
    Invoke-WebRequest $url -OutFile "$plik.part" -UseBasicParsing
    Move-Item "$plik.part" $plik -Force
}
function Rozpakuj($zip, $cel) {
    if (Test-Path $cel) { Remove-Item $cel -Recurse -Force }
    Expand-Archive $zip $cel -Force
}

try {
    Krok 1 'Karta graficzna'
    $nv = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if (-not $nv) { throw 'Nie znaleziono karty NVIDIA (brak nvidia-smi). Ten program działa tylko na kartach NVIDIA ze sterownikiem.' }
    & nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

    Krok 2 'uv (instalator Pythona)'
    $Uv = Join-Path $S 'uv\uv.exe'
    if (-not (Test-Path $Uv)) {
        Pobierz $UvUrl (Join-Path $Pobrane 'uv.zip')
        Rozpakuj (Join-Path $Pobrane 'uv.zip') (Join-Path $S 'uv')
    }
    & $Uv --version; Sprawdz 'uv'

    Krok 3 'Kod RelayVSR'
    if (-not (Test-Path (Join-Path $R 'inference.py'))) {
        Pobierz $RelayUrl (Join-Path $Pobrane 'relayvsr.zip')
        $tmp = Join-Path $Pobrane 'relayvsr'
        Rozpakuj (Join-Path $Pobrane 'relayvsr.zip') $tmp
        if (Test-Path $R) { Remove-Item $R -Recurse -Force }
        Move-Item (Join-Path $tmp "RelayVSR-$RelayCommit") $R
        Remove-Item $tmp -Recurse -Force
    }
    Write-Host '  jest'

    Krok 4 'Python 3.12 i paczki (PyTorch z CUDA, ok. 4,5 GB)'
    if (-not (Test-Path $Py)) {
        & $Uv venv (Join-Path $R '.venv') --python 3.12 --managed-python; Sprawdz 'tworzenie środowiska'
    }
    & $Uv pip install --python $Py 'torch==2.10.0' --index-url $TorchIndex; Sprawdz 'instalacja PyTorch'
    & $Uv pip install --python $Py -r (Join-Path $Baza 'wymagania.txt'); Sprawdz 'instalacja paczek'
    & $Py -I -c "import torch, tkinter; assert torch.cuda.is_available(), 'PyTorch nie widzi karty'; print('  PyTorch', torch.__version__, '-', torch.cuda.get_device_name(0))"
    Sprawdz 'PyTorch z CUDA'

    Krok 5 'Wagi modelu RelayVSR (ok. 9,5 GB, wznawia po przerwaniu)'
    & $Py -I -c "from huggingface_hub import hf_hub_download as d; [print('  ', d('kopper/RelayVSR', f, local_dir=r'$R\weights')) for f in ('flash.safetensors', 'wan.safetensors')]"
    Sprawdz 'pobieranie wag'

    Krok 6 'ffmpeg'
    $Ff = Join-Path $S 'ffmpeg\bin\ffmpeg.exe'
    if (Get-Command ffmpeg -ErrorAction SilentlyContinue) {
        Write-Host '  jest w systemie'
    } elseif (-not (Test-Path $Ff)) {
        Pobierz $FfmpegUrl (Join-Path $Pobrane 'ffmpeg.zip')
        $tmp = Join-Path $Pobrane 'ffmpeg'
        Rozpakuj (Join-Path $Pobrane 'ffmpeg.zip') $tmp
        $bin = Get-ChildItem $tmp -Recurse -Filter ffmpeg.exe | Select-Object -First 1
        New-Item -ItemType Directory -Force (Split-Path $Ff) | Out-Null
        Copy-Item (Join-Path $bin.DirectoryName '*') (Split-Path $Ff) -Force
        Remove-Item $tmp -Recurse -Force
        Write-Host "  zainstalowany w $(Split-Path $Ff)"
    } else {
        Write-Host '  jest w silniku'
    }

    # Skrót z ikoną obok skryptów (skrótów nie da się przenieść, więc tworzy go instalator)
    $sh = New-Object -ComObject WScript.Shell
    $lnk = $sh.CreateShortcut((Join-Path $Baza 'Enhance Vintage Milf.lnk'))
    $lnk.TargetPath = Join-Path $Baza 'Enhance Vintage Milf.cmd'
    $lnk.WorkingDirectory = $Baza
    $lnk.IconLocation = (Join-Path $Baza 'ikona.ico') + ',0'
    $lnk.Description = 'Powiększenie 4x, kolory, odszumianie, wyostrzanie i płynność 60/120 kl./s'
    $lnk.Save()

    Remove-Item $Pobrane -Recurse -Force -ErrorAction SilentlyContinue
    "Zainstalowane $(Get-Date -Format 'yyyy-MM-dd HH:mm')" | Set-Content $Znacznik -Encoding UTF8
    Write-Host "`nINSTALACJA GOTOWA" -ForegroundColor Green
    exit 0
} catch {
    Write-Host "`nBŁĄD: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host 'Uruchom ponownie - instalator dokończy od miejsca, w którym przerwał.'
    exit 1
}
