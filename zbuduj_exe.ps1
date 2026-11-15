# Kompiluje "Enhance Vintage Milf.exe" ze start\EnhanceVintageMilf.cs.
# Uzywa kompilatora C# z .NET Framework, ktory jest w kazdym Windows 10 i 11 - nic nie trzeba instalowac.
$ErrorActionPreference = 'Stop'
$Baza = $PSScriptRoot
$Csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path $Csc)) { throw "Nie ma kompilatora C# ($Csc)." }
$Wyjscie = Join-Path $Baza 'Enhance Vintage Milf.exe'
& $Csc /nologo /target:winexe /optimize+ /codepage:65001 `
    "/win32icon:$(Join-Path $Baza 'ikona.ico')" `
    /reference:System.Windows.Forms.dll /reference:System.Core.dll `
    "/out:$Wyjscie" (Join-Path $Baza 'start\EnhanceVintageMilf.cs')
if ($LASTEXITCODE -ne 0) { throw "Kompilacja nie powiodla sie (kod $LASTEXITCODE)." }
Write-Host "Gotowe: $Wyjscie"
